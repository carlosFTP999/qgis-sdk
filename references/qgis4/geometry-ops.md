# Geometry Operations

Geometry code fails silently when CRS, geometry type, or validity is ignored.
Check all three before calculating.

## Points and geometries

```python
from qgis.core import QgsGeometry, QgsPointXY

point = QgsGeometry.fromPointXY(QgsPointXY(10, 20))
buffer = point.buffer(5, 8)
centroid = buffer.centroid()
```

`buffer()` uses the layer CRS units. In a geographic CRS, a buffer of `5` is
five degrees, not five metres.

## CRS transformation

```python
from qgis.core import QgsCoordinateTransform, QgsProject

transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
geometry.transform(transform)
```

Transform before measuring, buffering, or comparing geometries from different
layers. Use a projected CRS for metric operations.

## Geometry types

```python
from qgis.core import Qgis

if geometry.type() == Qgis.GeometryType.Point:
    ...
```

Check the type before calling point-only, line-only, or polygon-only methods.
Multi-part geometries need explicit handling.

## Validity

```python
if not geometry.isGeosValid():
    repaired = geometry.makeValid()
```

Invalid polygons can make overlay and spatial-index operations unreliable.
Report how invalid geometries were handled.

## Spatial index

```python
from qgis.core import QgsSpatialIndex

index = QgsSpatialIndex(layer.getFeatures())
nearby = index.intersects(geometry.boundingBox())
```

Use a spatial index for repeated intersection or nearest-neighbour work. Do not
scan every feature for every geometry when an index is available.

## Overlay and proximity

```python
intersection = first.intersection(second)
distance = first.distance(second)
```

Handle empty geometries and `NULL` results. For nearest-neighbour work, use
`QgsSpatialIndex.nearestNeighbor()` and then verify the exact distance.

## Units

- Projected CRS: linear units, usually metres or feet.
- Geographic CRS: degrees; do not treat them as metres.
- `QgsDistanceArea` can compute ellipsoidal measurements when required.

## Performance

- Prefer `QgsSpatialIndex` over nested loops.
- Use `QgsFeatureRequest` with a bounding box or subset of attributes.
- Avoid creating a new transform for every feature when one transform can be
  reused.
- Check `feedback.isCanceled()` in long loops.

## Checklist

- [ ] Source and target CRS are known and valid.
- [ ] Data is transformed before metric operations.
- [ ] Geometry type is checked.
- [ ] Invalid geometries are handled or reported.
- [ ] Spatial index is used for repeated spatial queries.
- [ ] Empty results and `NULL` values are handled.

## Sources

- QGIS 3.44 API, `QgsGeometry`:
  https://qgis.org/pyqgis/3.44/core/QgsGeometry.html
- PyQGIS master API, `Qgis`:
  https://qgis.org/pyqgis/master/core/Qgis.html
