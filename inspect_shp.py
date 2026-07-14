import geopandas as gpd
import sys

path = sys.argv[1] if len(sys.argv)>1 else 'Example/Thailand.shp'
g = gpd.read_file(path)
print('CRS:', g.crs)
print('Columns:', list(g.columns))
print('Features:', len(g))
print('Geometry types:', g.geometry.geom_type.unique())
