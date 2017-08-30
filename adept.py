# Name:        planometric update workflow
# Purpose:     create .xls, pdfs, and gdb feature class for planometric updates
# Author:      brownr
# Created:     08/03/2016

# Import necessary modules
import arcpy
import datetime
import numpy
import os

# Create date stamp for today
today = str(datetime.date.today()).replace("-","_")

# Set all important datasets to a variable
# Root folder where all work will  be saved
rt_fldr = r"\\metanoia\geodata\PW\sw_tech\planometric_updates"

# SDE database
sde = r"C:\Users\brownr\AppData\Roaming\ESRI\Desktop10.3\ArcCatalog" \
       "\Connection to GISPRDDB direct connect.sde"
# gdb in root folder
gdb = rt_fldr+ r"\PLANOMETRIC_UPDATES.gdb"

# Create new folders based on date
# Create variable for new directory based on date
fldr = rt_fldr + "\\{0}".format(today)
exc_fldr = fldr + "\\excel"
pdf_fldr = fldr + "\\pdf"

# Create directory based on fldr
os.makedirs(fldr)
os.makedirs(exc_fldr)
os.makedirs(pdf_fldr)

# Designate output folder for excel sheet
excl = exc_fldr + "\\{0}.xls".format(today)

# Important features and tables
structures_change = sde + r"\cvGIS.CITY.Structure_Change"
parcel_area = sde + r"\cvgis.CITY.Cadastre\cvGIS.CITY.parcel_area"
parcel_point = sde + r"\cvgis.CITY.Cadastre\cvgis.CITY.parcel_point"

# Set mxds to variables
# Base map
bm = rt_fldr + r"\mxd\Planometric_Update_Basemap.mxd"
# Overview Map
ov = rt_fldr + "\mxd\Planometric_Updates_Overview.mxd"

# Make mxds accessable through arcpy
bm_mxd = arcpy.mapping.MapDocument(bm)
ov_mxd = arcpy.mapping.MapDocument(ov)

# Structure change table output
sc_table = gdb + r"\Test_" + today

# Where clause to select desired features from sc_table provided by Bart
sql_clause =  (
    "IN_SDE IS NULL AND NOT"
    "((Ltrim(rtrim(Type)) = 'C101 - SINGLE FAMILY DETACHED'"
    "OR Ltrim(rtrim(Type)) = 'C102 - SINGLE FAMILY ATTACHED'"
    "OR Ltrim(rtrim(Type)) = 'C103 -  TWO FAMILY'"
    "OR Ltrim(rtrim(Type)) = 'C104 -  THREE & FOUR FAMILY'"
    "OR Ltrim(rtrim(Type)) = 'C105 -  FIVE OR MORE FAMILY'"
    "OR Ltrim(rtrim(Type)) = 'C213 - HOTEL/MOTEL'"
    "OR Ltrim(rtrim(Type)) = 'C646 - DEMOLITION 2 FAMILY HOMES'"
    "OR Ltrim(rtrim(Type)) = 'EXTERIOR ACCESSORY APARTMENT'"
    "OR Ltrim(rtrim(Type)) = 'PRE-FABRICATED STRUCTURE'"
    "OR Ltrim(rtrim(Type)) = 'C318 - AMUSEMENT RECREATIONAL'"
    "OR Ltrim(rtrim(Type)) = 'C319 - CHRUCHES/RELIGIOUS'"
    "OR Ltrim(rtrim(Type)) = 'C320 - INDUSTRIAL'"
    "OR Ltrim(rtrim(Type)) = 'C322 - SERVICE STATION/REPAIR'"
    "OR Ltrim(rtrim(Type)) = 'C323 - HOSPITAL/INSTITUTION'"
    "OR Ltrim(rtrim(Type)) = 'C324 - OFFICE/BANK/PROFESSIONAL'"
    "OR Ltrim(rtrim(Type)) = 'C326 - SCHOOL/OTHER EDUCATIONAL'"
    "OR Ltrim(rtrim(Type)) = 'C327 - STORE/CUSTOMER SERVICES'"
    "OR Ltrim(rtrim(Type)) = 'C328 - OTHER NON-RESIDENTIAL'"
    "OR Ltrim(rtrim(Type)) = 'C329 - STRUCTURES OTHER-THAN BUILDINGS')"
    "OR isDemolition = 1)"
)

# Create access to Standalone Table by making it a TableView
aoi_table = arcpy.MakeTableView_management(structures_change, sc_table, \
                                           sql_clause)

# Get a list of unique PINs based on SDE Structure_Table query
data = arcpy.da.TableToNumPyArray(aoi_table, ['ParcelNumber'])
pin_list = numpy.unique(data['ParcelNumber'])

# Convert numpy.ndarray to string
val_list = []
for pin in pin_list:
    str_pin = str(pin)
    val_list.append(str_pin)

# Convert list of strings into one string to be used in query
val_list_as_str = "("
for val in val_list:
    val_list_as_str = val_list_as_str + "'" + val + "'" + ","
val_list_as_str = val_list_as_str[0:-1] + ")"

# Set destination for parcel area outfeature
suf = "\\Structure_Change_{0}".format(today)
feat = gdb + suf

# Create where clause for parcels of interest
aoi_whr_clause = "PIN In " + val_list_as_str


# Create new parcel feature based on result of query from SDE Structure_Table
parcel_area_aoi = arcpy.Select_analysis(parcel_area, feat, aoi_whr_clause)

# Join newly created parcel feature with queried Structure_Change table
joint_tbl = arcpy.JoinField_management(parcel_area_aoi,'PIN',sc_table,
                                       'ParcelNumber')

# Export attribute table to excel sheet
arcpy.TableToExcel_conversion(parcel_area_aoi, excl)

# Change old data source to new data source for AOI
lyr = arcpy.mapping.ListLayers(bm_mxd)[0]
lyr.replaceDataSource(gdb, 'FILEGDB_WORKSPACE', suf[1:], 'TRUE')

# Set data frame to AOI
df = arcpy.mapping.ListDataFrames(bm_mxd, "Layers")[0]

for val in val_list:
    where_clause = "PIN = '%s'" % val
    pdf = pdf_fldr + "\\PIN_" + val
    arcpy.SelectLayerByAttribute_management(lyr,"NEW_SELECTION", where_clause)
    df.zoomToSelectedFeatures()
    arcpy.SelectLayerByAttribute_management(lyr,"CLEAR_SELECTION")
    arcpy.mapping.ExportToPDF(bm_mxd, pdf)

# Create overview map
# Replace data source on AOI
ov_lyr = arcpy.mapping.ListLayers(ov_mxd)[0]
ov_lyr.replaceDataSource(gdb, 'FILEGDB_WORKSPACE', suf[1:], 'TRUE')

# Set data frame
ov_df = arcpy.mapping.ListDataFrames(ov_mxd, "Layers")[0]

# Zoom to AOI
ov_whr_clause = "IN_SDE IS NULL"
ov_pdf = pdf_fldr + "\\" + "Overview_Map"
arcpy.SelectLayerByAttribute_management(ov_lyr, "NEW_SELECTION", ov_whr_clause)
ov_df.zoomToSelectedFeatures()
arcpy.SelectLayerByAttribute_management(ov_lyr,"CLEAR_SELECTION")
arcpy.mapping.ExportToPDF(ov_mxd, ov_pdf)





