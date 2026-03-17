# Release Regression Checklist

Use this checklist before tagging a new add-on release.

## Preconditions

- Add-on image built from current branch and installable in Home Assistant.
- MQTT broker available.
- At least one ESP32 radio available; ideally two radios for multi-radio checks.
- Wii Remote paired for each active radio.

## 1. Clean Install

1. Install the add-on from the repository.
2. Configure one radio and enable `discover_enabled: true`.
3. Start add-on and verify logs show MQTT connected before discovery publication.
4. Verify Home Assistant entities appear for:
   - one connectivity binary sensor
   - one battery sensor
   - one button binary sensor per supported button
5. Verify button entities and raw MQTT button topics both update on press/release.

## 2. Add-on Restart

1. Restart only the add-on.
2. Verify startup logs include discovery publication summary.
3. Verify entities remain available and continue updating.
4. Verify no duplicate entities are created.

## 3. MQTT Broker Restart

1. Restart broker while add-on remains running.
2. Verify add-on logs disconnect and reconnect.
3. Verify discovery publication runs after reconnect.
4. Verify entity states resume updates.

## 4. Home Assistant Restart

1. Restart Home Assistant core while broker and add-on remain running.
2. Verify entities are restored from retained discovery topics.
3. Verify no immediate manual republish action is required.

## 5. Broker Outage and Recovery

1. Stop broker temporarily.
2. Trigger button presses while broker is down.
3. Verify disconnected publish warnings appear (rate-limited).
4. Restore broker.
5. Verify reconnect and discovery republish logs.
6. Verify live updates resume for entities and raw topics.

## 6. Multiple Radios

1. Configure at least two radios with distinct `controller_id` values.
2. Restart add-on.
3. Verify discovery entities are created per controller ID.
4. Verify button presses from each controller only update matching controller topics/entities.
5. Verify battery and connected status are independent per controller.

## 7. Retained Discovery Verification

1. Query retained discovery topics:

    ```bash
    mosquitto_sub -h <broker-host> -p <broker-port> -u <user> -P <pass> -v -R -t 'homeassistant/+/wiimote_+/+/config'
    ```

2. Verify retained config topics exist for connected, battery, and all supported buttons for each controller.
3. Validate payload state topics map to expected runtime topics.

## 8. Raw Topic Sanity

1. Subscribe to runtime topics:

    ```bash
    mosquitto_sub -h <broker-host> -p <broker-port> -u <user> -P <pass> -v -t 'wiimote/#'
    ```

2. Verify these topic families are active:
   - `<topic_prefix>/<id>/button/<BUTTON>`
   - `<topic_prefix>/<id>/status/connected`
   - `<topic_prefix>/<id>/status/battery`
   - `<topic_prefix>/<id>/status/heartbeat`
   - `<topic_prefix>/<id>/events/<type>`

## Pass Criteria

- Discovery entities appear and remain stable across restarts/reconnects.
- No duplicate entities are created.
- Raw topics continue to publish expected payloads.
- Multi-radio routing stays isolated by `controller_id`.
