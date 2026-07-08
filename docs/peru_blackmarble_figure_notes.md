# Peru Black Marble figure notes

## Transformation

The Peru example uses:

```text
log(1 + 1000 × mean daily radiance)
```

This follows the same harmonized scale used for the Indonesia and Bolivia daily Black Marble figures. Keeping the transformation and y-axis fixed makes cross-country visual comparison easier.

## Spaghetti plot note

Thin colored lines show daily trajectories for individual Peruvian districts. Colors follow long-run district brightness using the plasma palette. The thick line shows the simple daily average across districts. Transformation: `log(1 + 1000 × mean daily radiance)`. The y-axis is fixed from 0 to 16 to make figures directly comparable across countries. Blank vertical gaps correspond to days with no valid district-level observations after Black Marble quality filtering and zonal statistics.

## Fan chart note

The decile fan chart summarizes the daily cross-sectional distribution of Peruvian districts. Bands show adjacent decile intervals of the transformed outcome, from the lower tail in blue tones to the upper tail in warm orange-red tones; middle deciles are shown in yellow. Transformation: `log(1 + 1000 × mean daily radiance)`. The y-axis is fixed from 0 to 16 to make the Peru, Indonesia, and Bolivia figures directly comparable. Blank vertical gaps correspond to days with no valid district-level observations after Black Marble quality filtering and zonal statistics.

## Interpretation guide

The spaghetti plot is useful for seeing the full mass of district-level trajectories, unusual units, shared movements, visible breaks, and the envelope of the panel.

The descriptive fan chart is useful for comparing the stability of different parts of the distribution. It can reveal patterns that are hard to see in the spaghetti plot, such as whether lower-light districts are more unstable than brighter districts or whether the upper deciles remain comparatively stable over time.

## Time frequency support

The package accepts daily, monthly, and annual panel time variables. Daily dates can be passed as ordinary date strings or datetimes. Monthly panels can use month-year strings such as `2020-05` or `2020/05`. Annual panels can use numeric years such as `2020`. For fan charts, `freq="auto"` is the default and completes the time grid using daily (`D`), month-start (`MS`), or year-start (`YS`) frequency when it can infer the structure.
