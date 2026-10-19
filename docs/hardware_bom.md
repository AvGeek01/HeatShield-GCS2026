# HeatShield Delhi Pilot Sensor Node BOM

Planning BOM for six low-cost outdoor nodes for the DTU/Rohini pilot. Prices
are INR per node, checked against Indian supplier listings on **19 October
2026** where possible; vendor prices, stock, shipping, and taxes can change.
Prices below include GST when the listing says so. No bulk discount, assembly,
mounting labor, or delivery charge is assumed.

## Per-node bill of materials

| Item | Recommended choice | INR / node | Price basis and supplier |
| --- | --- | ---: | --- |
| Controller | ESP32-WROOM-32 38-pin development board | 449 | [Robu listing](https://robu.in/product/esp32-38pin-development-board-wifibluetooth-ultra-low-power-consumption-dual-core/), listed with GST |
| Temperature and humidity | SHT31 module preferred; DHT22 is lower-cost fallback | 399 (SHT31) / 119 (DHT22) | [Robu GY-SHT31-D](https://robu.in/product/unwelded-gy-sht31-d-digital-temperature-and-humidity-sensor/) was listed at ₹399 but out of stock; [DHT22 module](https://robu.in/product/dht22-digital-temperature-humidity-sensor-temperature-humidity-module-am2302/) listed at ₹119 |
| Ambient light | GY-30 BH1750 module | 129 | [Robu listing](https://robu.in/product/gy-30-bh1750fvi-digital-light-intensity-illumination-sensor/) |
| Battery cell | One reputable 18650 cell, 2,600 mAh class | 229 | [Robu BAK 18650, 2,600 mAh](https://robu.in/product/bak-nmc-18650-2600mah-3c-lithium-ion-3-6v-battery/), listed with GST |
| Battery holder and protection | Single-cell holder plus correctly rated 1S protection and solar Li-ion charge circuitry | 100-250 | Planning allowance; [Robu 1S 5A protection board](https://robu.in/product/1s-5a-18650-lithium-battery-protection-board/) was listed at ₹49; holder and charge circuit vary |
| Solar panel | 3-5 W, nominal 6 V panel sized for measured duty cycle | 350-600 | Planning allowance; a [Robu 0.45 W / 3 V panel](https://robu.in/product/0-45w-3v-150ma-mini-solar-panel-8x6-cm/) was listed at ₹156 but out of stock and is not sized as the default recommendation |
| Radiation shield | White, naturally ventilated multi-plate shield; DIY UV-stable plates and spacers | 150-300 | Fabrication allowance; no low-cost shield listing with a verifiable price was found. Commercial shields are much more expensive |
| Enclosure, cable glands, mast clamp, fasteners, wiring | Weather-resistant enclosure for electronics; keep sensing element ventilated and outside the enclosure | 250-450 | Planning allowance; confirm enclosure IP rating, UV resistance, and mounting locally |

**Estimated SHT31 build:** ₹2,056-2,606 per node, or **₹12,336-15,636 for
six**. Add ₹200-500 per node for an optional black-globe temperature channel,
making the six-node total approximately **₹13,536-18,636**. The DHT22 fallback
reduces the estimate by about ₹280 per node. These totals are planning estimates,
not a purchase quote; confirm supplier stock and get a quote for the shield,
panel, enclosure, and charger before procurement.

## Optional globe thermometer channel

For heat-stress field validation, add a small matte-black globe (roughly 40 mm
is a practical compact prototype) with a thermistor or waterproof digital
temperature probe mounted at its center. Allow ₹200-500 per node for the globe,
sensor, and wiring. This is a DIY comparative measurement, **not a calibrated
standard globe thermometer**; document diameter, coating, sensor placement,
response time, and calibration against a reference before using it in derived
WBGT. Omit it on nodes where cost or power is limiting.

## Six-node purchasing and deployment notes

- Buy six of the controller, light sensor, cell, protection/charging parts,
  shield, and enclosure. For the humidity sensor, use SHT31 if a stocked module
  is available at ordering time; otherwise keep DHT22 nodes identified in the
  data so sensor-specific calibration is applied.
- Solar sizing depends on radio duty cycle, shade, panel orientation, and
  winter/cloud performance. Measure node current in sleep and transmit states
  first. Use a charge controller intended for a single-cell Li-ion battery,
  plus cell protection; do not connect a panel directly to an 18650 cell.
- ESP32 Wi-Fi transmission can dominate the energy budget. Batch readings,
  use deep sleep, and verify several overcast days of autonomy. Provide a secure
  pole mount and tamper-resistant enclosure for public-space installation.
- Place the temperature/humidity element in the ventilated radiation shield,
  separated from the ESP32, regulator, battery, and solar panel heat. Do not
  place the BH1750 behind tinted plastic. Log sensor model and calibration
  metadata with each node.
- These nodes are pilot-grade environmental monitors, not certified weather
  stations or medical instruments. Keep the existing forecast and risk output
  clearly labeled as estimates until field validation is complete.

## Supplier source notes

All linked commercial items above are from Robu.in, an Indian electronics
retailer. The supplier pages displayed current listing prices when checked;
some clearly showed out-of-stock status as noted. Re-open product links before
ordering because listing price and availability can change. Prices shown are
not contractual and exclude shipping. The radiation shield, compact 3-5 W
panel, accessories, and optional globe build are explicitly budget allowances,
not externally verified vendor quotations.