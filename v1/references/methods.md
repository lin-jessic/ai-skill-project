# Methods / interpretation

- Time distribution uses the parsed local accident hour; count unit is a row or a verified event record, not automatically a unique accident.
- Hotspots use a regular latitude/longitude grid, resolution 0.005 degrees; this is a reproducible visualization unit, not a legal road segment.
- Map filters latitude in [21.5,25.5] and longitude in [119,123] (Taiwan main island and some surrounding coverage); out-of-range values are excluded from map but may remain in non-spatial totals.
- The word 'historical collision concentration' is mandatory. Without traffic counts, different road lengths/exposure or normalized travel distance, no causal road risk ranking can be claimed.
- The dataset has no direct identification of a patient's treatment, transfer destination or hospitalization. These cannot be inferred.
- Weather counts reflect observed incidents under that weather; not per-hour weather-adjusted risk.
- Aggregate counts only; prevent personal identification in exports.
