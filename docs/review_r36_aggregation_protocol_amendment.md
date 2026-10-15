# M1 aggregation protocol amendment

The project owner explicitly discontinued both PASTA and TANGO. This is a
documented change to the project protocol, not evidence of absent aggregation
hotspots and not completion of the unamended original proposal.

`M1V3Rules.aggregation_exclusion_reference` accepts the explicit amendment
reference. Without it, the original aggregation evidence requirement is
unchanged. With it, the workflow omits only the aggregation prediction node and
reports `excluded_checks.full_fusion_aggregation`; the hotspot observation stays
missing, not zero. SignalP, DeepTMHMM, identity and localization checks remain
required. This flag does not approve any construct, LLPS result or M2 result.

Server-only regression of `tests/test_m1_completion.py`: 8 tests passed. These
are contract fixtures, not experimental or native predictor validation.
