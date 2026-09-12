# rumqtt

[bytebeamio/rumqtt](https://github.com/bytebeamio/rumqtt).

## What is tested

**`src/mqttbytes/mod.rs`**
- `remaining_length_encode_decode_roundtrip`: (no doc comment)
- `remaining_length_above_max_is_rejected`: (no doc comment)
- `length_decode_never_panics_and_stays_in_range`: (no doc comment)

**`src/mqttbytes/topic.rs`**
- `derived_wildcard_filters_are_valid`: (no doc comment)
- `topic_matches_filter_derived_from_it`: (no doc comment)
- `known_failure_matches_never_panics_on_multibyte_topics`: KNOWN FAILURE: `matches()` slices `topic[..1]` by *byte* index to test for a leading '$'. If the topic starts with a multi-byte UTF-8 character (e.g. "über/temp"), this panics on a char boundary error instead of matching. It should use `starts_with('$')`.

**`src/mqttbytes/v4/mod.rs`**
- `v4_packet_write_read_roundtrip`: (no doc comment)
- `v4_size_agrees_with_write`: (no doc comment)
- `v4_read_never_panics_on_arbitrary_bytes`: (no doc comment)
- `v4_truncated_packet_reports_insufficient_bytes`: (no doc comment)
- `v4_incoming_max_packet_size_is_honored`: (no doc comment)
- `v4_outgoing_max_packet_size_is_honored`: (no doc comment)
- `v4_packet_sequence_roundtrip`: Writing several packets into one buffer and decoding them back (the tokio codec usage pattern). Connect packets are only generated in first position here: `Connect::write` corrupts the buffer when it doesn't start at offset 0, see `known_failure_v4_connect_written_after_another_packet_roundtrips`.
- `known_failure_v4_publish_topic_longer_than_u16_roundtrips`: KNOWN FAILURE: `write_mqtt_bytes` casts the data length to u16, so any string/bytes field of 65536+ bytes gets a truncated length prefix while the full data is still written. `Packet::write` reports success but the produced frame decodes to a *different* packet (or garbage). It should return an error for fields that don't fit in the u16 length prefix.
- `known_failure_v4_connect_written_after_another_packet_roundtrips`: KNOWN FAILURE: `Connect::write` computes `flags_index` relative to the start of the buffer instead of the start of the packet, so writing a Connect into a buffer that already contains bytes patches the connect flags into the wrong position, corrupting the stream. (The v5 `Connect::write` in src/v5/mqttbytes/v5/connect.rs has the same bug.)

**`src/v5/mqttbytes/v5/mod.rs`**
- `v5_read_never_panics_on_arbitrary_bytes`: (no doc comment)
- `known_failure_v5_connect_written_after_another_packet_roundtrips`: KNOWN FAILURE: like its v4 counterpart (see `known_failure_v4_connect_written_after_another_packet_roundtrips` in src/mqttbytes/v4/mod.rs), the v5 `Connect::write` computes `flags_index` relative to the buffer start instead of the packet start, so a Connect written into a non-empty buffer patches its connect flags into the wrong byte and corrupts the stream.

**`src/v5/mqttbytes/v5/publish.rs`**
- `v5_publish_write_read_roundtrip`: (no doc comment)
- `v5_publish_size_agrees_with_write`: (no doc comment)
- `known_failure_v5_publish_multiple_subscription_ids_roundtrip`: KNOWN FAILURE: `PublishProperties::read` double-counts the property-type byte for subscription identifiers (`cursor += 1 + id_len` after `cursor += 1` was already applied at the top of the loop, see src/v5/mqttbytes/v5/publish.rs:229). With three or more subscription identifiers the cursor overruns the property length, the loop exits early, and the remaining property bytes are misparsed as payload. `SubscribeProperties::read` (src/v5/mqttbytes/v5/subscribe.rs:237) has the same double-count, marked with a TODO.
- `v5_truncated_publish_reports_insufficient_bytes`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-05-01: predecessor base commit `e886a788935d` (feat: add support for binding outgoing TCP connections to a specifi...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rumqtt.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
