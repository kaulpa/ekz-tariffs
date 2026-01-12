# EKZ Dynamic Tariffs

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![GitHub Release](https://img.shields.io/github/v/release/schmidtfx/ekz-tariffs)
![GitHub License](https://img.shields.io/github/license/schmidtfx/ekz-tariffs)

This is the EKZ tariffs API integration for Home Assistant.

## Features

- Let's you pick your energy tariff
- Refreshes latest energy prices every day at 6:30pm.
- Let's you customize all entities this integration provides (every entity has a unique ID)
- Provides current energy price
- Provides a timestamp for the next change of the energy price
- Provides sensors to indicate the most expensive and cheapest hours for today and tomorrow

## Installation

There are two ways this integration can be installed into Home Assistant.

The easiest and recommended way is to install the integration using HACS, which makes future updates easy to track and install.

Alternatively, installation can be done manually copying the files in this repository into `custom_components` directory in the Home Assistant configuration directory:

1. Open the configuration directory of your Home Assistant installation.
2. If you do not have a custom_components directory, create it.
3. In the custom_components directory, create a new directory called `ekz_tariffs`.
4. Copy all files from the `custom_components/ekz_tariffs/` directory in this repository into the `ekz_tariffs` directory.
5. Restart Home Assistant.
6. Add the integration to Home Assistant (see **Configuration**).

## Configuration

Configuration is done through the Home Assistant UI.

To add the integration, go to **Settings** ➤ **Devices & Services** ➤ **Integrations**, click ➕ **Add Integration**, and search for "EKZ Dynamic Tariffs".

### Configuration Variables

| Name | Type | Default | Description |
| :--- | :--- | :------ | :---------- |
| `tariff_name` | `enum` | `400D` | 400D, 400F, 400ST, 400WP, 400L, 400LS, 16L, 16LS |

## Service Actions

### EKZ Tariffs: Refresh

`ekz_tariffs.refresh`

Triggers an update of the energy prices.