# hass-MinerMonitor

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance1-shield]][user1_profile]
[![Project Maintenance][maintenance2-shield]][user2_profile]
[![Project Maintenance][maintenance3-shield]][user3_profile]

Control and monitor your Bitcoin Miners from Home Assistant.

Great for Heat Reusage, Solar Mining, or any use case where you don't need your miners running 24/7 or with a specific wattage.

Works great in coordination with [ESPHome](https://www.home-assistant.io/integrations/esphome/) for Sensors (like temperature) and [Grafana](https://github.com/hassio-addons/addon-grafana) for Dashboards.

### Support for:

- Antminers
- Whatsminers
- Avalonminers
- Innosilicons
- Goldshells
- Auradine
- BitAxe
- IceRiver
- Hammer
- Braiins Firmware
- Vnish Firmware
- ePIC Firmware
- HiveOS Firmware
- LuxOS Firmware
- Mara Firmware

[Full list of supported miners](https://pyasic.readthedocs.io/en/latest/miners/supported_types/).

**This component will set up the following platforms -**

| Platform | Description               |
| -------- | ------------------------- |
| `sensor` | Show info from miner API. |
| `number` | Set Power Limit of Miner. |
| `switch` | Switch Miner on and off   |

**This component will add the following services -**

| Service           | Description                          |
| ----------------- | ------------------------------------ |
| `reboot`          | Reboot a miner by IP                 |
| `restart_backend` | Restart the backend of a miner by IP |

---

## Recent Fixes and Improvements

### 1. Enhanced Sensor and Coordinator Data Handling
- **Improvement**: Added new sensors (`uptime`, `percent_expected_hashrate`, `env_temp`, `errors`, `fault_light`) and ensured they are correctly defined and handled.

### 2. Improved Error Handling
- **Improvement**: Added clearer processing for miner data errors.

### 3. Consistent Entity Availability Checks
- **Improvement**: Ensured all entities have consistent `available` property implementations referencing the coordinator’s availability status.

### 4. Clarified Board Indexing Logic
- **Improvement**: Documented and distinguished between hardware board indices (`board_num`) and Home Assistant-friendly indices (`display_idx`).

### 5. Verified `device_info` Structure
- **Improvement**: Ensured consistent and complete definitions of `device_info` for all sensor types.

---

## Using the Integration

### Correcting Hashrate for Antminer E9 Pro
TAntminer E9 Pro hashrate is reported in TH/s, which is 1000x too high. Use the following template in your `configuration.yaml` to correct the hashrate:

```yaml
template:
  sensor:
    - name: "Antminer E9 Corrected Hashrate"
      unit_of_measurement: "MH/s"
      device_class: power
      state_class: measurement
      state: >
        {% set raw = states('sensor.antminer_e9_hashrate') | float(0) %}
        {% if raw > 0 %}
          {{ (raw / 1000) | round(0) }}
        {% else %}
          0
        {% endif %}
```

### Automating Miner Reset on Failure
To automatically reboot the Antminer E9 Pro in case of malfunction, use the following automation in your `automations.yaml`:

```yaml
alias: Reset Antminer E9 Pro on Failure
description: Automatically reboot the E9 Pro if the hashrate remains below 400 MH/s for more than 120 seconds and uptime exceeds 1600 seconds.
trigger:
  - platform: numeric_state
    entity_id: sensor.antminer_e9_hashrate
    below: 400
    for:
      seconds: 120
condition:
  - condition: numeric_state
    entity_id: sensor.antminer_e9_uptime
    above: 1600
action:
  - service: miner.reboot
    target:
      device_id: <your_device_id_here>
mode: single
```

**Note**: The uptime threshold of 1600 seconds accounts for the time required to create the DAG file. Adjust this value based on the blockchain you are mining.

Here's an automation example for Antminer D7. You probably don't need the "condition:" block but it's probably a good idea to give 2-3 min slack for good measure.

```yaml
alias: Reset Antiminer D7 on Failure
description: Automatically reboot D7 if the hashrate remains below 400 GH/s for more than 120 seconds and uptime exceeds 120 seconds.
triggers:
  - entity_id: sensor.antminer_d7_hashrate
    below: 400
    for:
      seconds: 120
    trigger: numeric_state
conditions:
  - type: is_value
    condition: device
    entity_id: sensor.antminer_d7_uptime
    device_id: <your_device_id_here>
    domain: sensor
    above: 120
actions:
  - action: miner.reboot
    metadata: {}
    data: {}
    target:
      device_id: <your_device_id_here>
mode: single
```

---

## Installation

Use HACS, add the custom repo https://github.com/Schnitzel/hass-miner to it.

[![Installation and usage Video](http://img.youtube.com/vi/eL83eYLbgQM/0.jpg)](https://www.youtube.com/watch?v=6HwSQag7NU8)

---

## Contributions are welcome!

If you want to contribute to this, please read the [Contribution guidelines](CONTRIBUTING.md).

---

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template.

Miner control and data is handled using [@UpstreamData](https://github.com/UpstreamData)'s [pyasic](https://github.com/UpstreamData/pyasic).

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/Schnitzel/hass-miner.svg?style=for-the-badge
[commits]: https://github.com/Schnitzel/hass-miner/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/Schnitzel/hass-miner.svg?style=for-the-badge
[maintenance1-shield]: https://img.shields.io/badge/maintainer-%40Schnitzel-blue.svg?style=for-the-badge
[maintenance2-shield]: https://img.shields.io/badge/maintainer-%40b--rowan-blue.svg?style=for-the-badge
[maintenance3-shield]: https://img.shields.io/badge/maintainer-%40nikolaos83-blue.svg?style=for-the-badge
[user1_profile]: https://github.com/Schnitzel
[user2_profile]: https://github.com/b-rowan
[user3_profile]: https://github.com/nikolaos83