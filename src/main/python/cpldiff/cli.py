#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) Sandflow Consulting LLC
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import xml.etree.ElementTree as et
import argparse
import re
import logging
import typing
from fractions import Fraction
import difflib
import sys

LOGGER = logging.getLogger(__name__)

def split_qname(qname: str):
  m = re.match(r'\{(.*)\}(.*)', qname)
  return (m.group(1) if m else None, m.group(2) if m else None)

def cpl_rational_to_fraction(r: str) -> Fraction:
  return Fraction(*map(int, r.split()))

COMPATIBLE_CPL_NS = set((
  "http://www.smpte-ra.org/schemas/2067-3/2016",
  "http://www.smpte-ra.org/schemas/2067-3/2013"
))

COMPATIBLE_CORE_NS = set((
  "http://www.smpte-ra.org/schemas/2067-2/2013",
  "http://www.smpte-ra.org/schemas/2067-2/2016",
  "http://www.smpte-ra.org/ns/2067-2/2020"
))

class CPL:

  main_image_edit_unit: typing.List[str]
  edit_rate: Fraction

  def get_edit_rate(self) -> Fraction:
    return self.edit_rate

  def __len__(self):
    return len(self.main_image_edit_unit)

  def __getitem__(self, key):
    return self.main_image_edit_unit[key]

  def __init__(self, cpl_doc) -> None:

    self.main_image_edit_unit = []

    namespace, local_name = split_qname(cpl_doc.tag)

    if namespace not in COMPATIBLE_CPL_NS:
      LOGGER.error("Unknown CompositionPlaylist namespace: %s", namespace)

    if local_name != "CompositionPlaylist":
      LOGGER.error("Unknown CompositionPlaylist element name: %s", local_name)

    ns_dict = {"cpl": namespace}

    self.edit_rate = cpl_rational_to_fraction(cpl_doc.findtext(".//cpl:EditRate", namespaces=ns_dict))

    sequence_list = cpl_doc.find("./cpl:SegmentList/cpl:Segment/cpl:SequenceList", namespaces=ns_dict)

    for sequence in sequence_list:
      track_id = sequence.findtext("cpl:TrackId", namespaces=ns_dict)

      if track_id is None:
        LOGGER.error("Sequence is missing TrackId")
        continue

      sequence_ns, sequence_name = split_qname(sequence.tag)

      if sequence_ns not in COMPATIBLE_CORE_NS:
        LOGGER.warning("Unknown virtual track namespace %s", sequence_ns)
        continue

      if sequence_name != "MainImageSequence":
        continue

      resources = cpl_doc.findall(
        f"./cpl:SegmentList/cpl:Segment/cpl:SequenceList/*[cpl:TrackId='{track_id}']/cpl:ResourceList/cpl:Resource",
        namespaces=ns_dict)

      for resource in resources:

        entry_point = int(resource.findtext(".//cpl:EntryPoint", namespaces=ns_dict) or 0)
        resource_duration = int(resource.findtext(".//cpl:SourceDuration", namespaces=ns_dict) or \
          resource.findtext(".//cpl:IntrinsicDuration", namespaces=ns_dict))
        repeat_count = int(resource.findtext(".//cpl:RepeatCount", namespaces=ns_dict) or 1)
        trackfile_id = resource.findtext(".//cpl:TrackFileId", namespaces=ns_dict)

        for _ in range(repeat_count):
          for edit_unit_index in range(entry_point, entry_point + resource_duration):
            self.main_image_edit_unit.append(
              (
                edit_unit_index,
                trackfile_id
              )
            )

def main():
  parser = argparse.ArgumentParser(description="Computes the difference between the timelines of two IMF Compositions")
  parser.add_argument('cpl_old', type=argparse.FileType(mode='r',encoding="UTF-8"), help='Path to the first CPL document')
  parser.add_argument('cpl_new', type=argparse.FileType(mode='r',encoding="UTF-8"), help='Path to the second CPL document')
  args = parser.parse_args()

  cpl_old = CPL(et.parse(args.cpl_old).getroot())
  cpl_new = CPL(et.parse(args.cpl_new).getroot())

  if cpl_old.get_edit_rate() != cpl_new.get_edit_rate():
    LOGGER.error("The two Compositions do not have identical edit rates.")
    sys.exit(1)

  d = difflib.SequenceMatcher(a=cpl_old, b=cpl_new, autojunk=False)

  for tag, i1, i2, j1, j2 in d.get_opcodes():
    print('{:7} [{}:{}] --> [{}:{}]'.format(tag, i1, i2, j1, j2))

if __name__ == "__main__":
  main()
