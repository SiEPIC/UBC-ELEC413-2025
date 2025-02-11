
'''
Script to create a layout:

DFB Laser integrated with Photonic Wire Bonds
Splitter tree using 1x2 splitters
Aggregating submitted designs

by Lukas Chrostowski, Sheri, 2022-2025

using SiEPIC-Tools

For more information on scripting:
  https://github.com/SiEPIC/SiEPIC-Tools/wiki/Scripted-Layout
  
usage:
 - run this script, inside KLayout Application, or externally using PyPI package
   - requires siepicfab_ebeam_zep PyPI package 

Install the PDK for develpers:
# cd ... GitHub/SiEPICfab-EBeam-ZEP-PDK
# pip install -e .

 
'''

import siepicfab_ebeam_zep

# Debugging run, or complete
draw_waveguides = True
run_number_designs = 100

# Configuration for the Technology to use
tech = ["SiEPICfab_EBeam_ZEP"]
tech = tech[0]

# Configuration for the arrangement
n_lasers = 3
tree_depth = 4 
die_size = 7800000

waveguide_type={'SiEPICfab_Shuksan_PDK':'Strip TE 1310 nm, w=350 nm', 
                'SiEPICfab_EBeam_ZEP':'Strip TE 1310 nm, w=350 nm (core-clad)'}

blank_design = "design_ZZZ"  # Python design file, otherwise None for terminator.

waveguide_pitch = 8
dy_gcs = 127e3 # pitch of the fiber array
pad_pitch = 250000
metal_width = 20000
metal_width_laser = 50000
metal_width_laser_heater = 20000

# configuration
top_cell_name = 'Shuksan_2025_02'
cell_Width = 605000
cell_Height = 410000
cell_Gap_Width = 8000
cell_Gap_Height = 8000
chip_Width = 8650000
chip_Height1 = 8490000
chip_Height2 = 8780000
br_cutout_x = 7484000
br_cutout_y = 898000
br_cutout2_x = 7855000
br_cutout2_y = 5063000
tr_cutout_x = 7037000
tr_cutout_y = 8494000
die_edge = 0

filename_out = 'Shuksan'
layers_keep = ['1/0', '1/2', '100/0', '101/0', '1/10', '68/0', '81/0', '10/0', '99/0', '200/0', '11/0', '201/0', '6/0', '998/0']
layer_text = '10/0'
layer_SEM = '200/0'
layer_SEM_allow = ['edXphot1x', 'ELEC413','SiEPIC_Passives']  # which submission folder is allowed to include SEM images
layers_move = [[[31,0],[1,0]]] # move shapes from layer 1 to layer 2
dbu = 0.001
log_siepictools = False
framework_file = 'Framework'
ubc_file = 'UBC_static.oas'


# record processing time
import time
start_time = time.time()
from datetime import datetime
now = datetime.now()




# SiEPIC-Tools initialization
import pya
from pya import *
import SiEPIC
from packaging.version import Version
from SiEPIC._globals import Python_Env, KLAYOUT_VERSION, KLAYOUT_VERSION_3
if Version(SiEPIC.__version__) < Version('0.5.14'):
    raise Exception ('This PDK requires SiEPIC-Tools v0.5.14 or greater.')
from SiEPIC import scripts  
from SiEPIC.utils import get_layout_variables
from SiEPIC.scripts import connect_pins_with_waveguide, connect_cell, zoom_out, export_layout
from SiEPIC.utils.layout import new_layout, floorplan
from SiEPIC.utils import get_technology_by_name
from SiEPIC.extend import to_itype

'''
Create a new layout
with a top cell
and Draw the floor plan
'''    
top_cell, ly = new_layout(tech, top_cell_name, GUI=True, overwrite = True)
layout = ly
dbu = ly.dbu
layerText = pya.LayerInfo(int(layer_text.split('/')[0]), int(layer_text.split('/')[1]))
layerTextN = top_cell.layout().layer(layerText)

TECHNOLOGY = get_technology_by_name(tech)
if TECHNOLOGY['technology_name'] not in tech or not tech in pya.Technology.technology_names():
    raise Exception ('This example needs to be executed in a layout with Technology = %s' % tech)
else:
    waveguide_type = waveguide_type[tech]


'''
# Floorplan
die_edge = int(die_size/2)
box = Box( Point(-die_edge, -die_edge), Point(die_edge, die_edge) )
top_cell.shapes(ly.layer(TECHNOLOGY['FloorPlan'])).insert(box)
'''



# path for this python file
import os
path = os.path.dirname(os.path.realpath(__file__))

# Log file
global log_file
log_file = open(os.path.join(path,filename_out+'.txt'), 'w')
def log(text):
    global log_file
    log_file.write(text)
    log_file.write('\n')

log('SiEPIC-Tools %s, layout merge, running KLayout 0.%s.%s ' % (SiEPIC.__version__, KLAYOUT_VERSION,KLAYOUT_VERSION_3) )
current_time = now.strftime("%Y-%m-%d, %H:%M:%S local time")
log("Date: %s" % current_time)

# Load all the GDS/OAS files from the "submissions" folder:
path2 = os.path.abspath(os.path.join(path,"../submissions"))
files_in = []
_, _, files = next(os.walk(path2), (None, None, []))
for f in sorted(files):
    files_in.append(os.path.join(path2,f))

# Load all the GDS/OAS files from the "framework" folder:
path2 = os.path.abspath(os.path.join(path,"../framework"))
_, _, files = next(os.walk(path2), (None, None, []))
for f in sorted(files):
    files_in.append(os.path.join(path2,f))

# Create course cells using the folder name under the top cell
cell_edXphot1x = layout.create_cell("edX")
t = Trans(Trans.R0, 0,0)
top_cell.insert(CellInstArray(cell_edXphot1x.cell_index(), t))
cell_ELEC413 = layout.create_cell("ELEC413")
top_cell.insert(CellInstArray(cell_ELEC413.cell_index(), t))
cell_SiEPIC_Passives = layout.create_cell("SiEPIC_Passives")
top_cell.insert(CellInstArray(cell_SiEPIC_Passives.cell_index(), t))
cell_openEBL = layout.create_cell("openEBL")
top_cell.insert(CellInstArray(cell_openEBL.cell_index(), t))

# Create a date	stamp cell, and add a text label
merge_stamp = '.merged:'+now.strftime("%Y-%m-%d-%H:%M:%S")
cell_date = layout.create_cell(merge_stamp)
text = Text (merge_stamp, Trans(Trans.R0, 0, 0) )
shape = cell_date.shapes(layout.layer(10,0)).insert(text)
top_cell.insert(CellInstArray(cell_date.cell_index(), t))   

# load the cells from the PDK
if tech == "SiEPICfab_EBeam_ZEP":
    library = tech
    library_beta = "SiEPICfab_EBeam_ZEP_Beta"
    # library_ubc = "SiEPICfab_EBeam_ZEP_UBC"
    cell_y = ly.create_cell('ybranch_te1310', library)
    #cell_splitter = ly.create_cell('splitter_2x2_1310', library)
    #cell_heater = ly.create_cell('wg_heater', library)
    #cell_waveguide = ly.create_cell('ebeam_pcell_taper',library, {
        #'wg_width1': 0.35,
        #'wg_width2': 0.352})
    cell_waveguide = ly.create_cell('Waveguide_Straight',library_beta, {
        'wg_length': 40,
        'wg_width': 350})
    # cell_waveguide = ly.create_cell('w_straight',library)
    #cell_pad = ly.create_cell('ebeam_BondPad', library)
    cell_gcA = ly.create_cell('GC_Air_te1310_BB', library)
    cell_gcB = ly.create_cell('GC_Air_te1310_BB', library)
    cell_terminator = ly.create_cell('terminator_te1310', library)
    cell_laser = ly.create_cell('laser_1310nm_DFB_BB', library_beta)
    metal_layer = "M1"
    cell_taper = ly.create_cell('ebeam_taper_350nm_2000nm_te1310', library_beta)

if not cell_y:
    raise Exception ('Cannot load 1x2 splitter cell; please check the script carefully.')
#if not cell_splitter:
#    raise Exception ('Cannot load 2x2 splitter cell; please check the script carefully.')
if not cell_taper:
    raise Exception ('Cannot load taper cell; please check the script carefully.')
if not cell_gcA:
    raise Exception ('Cannot load grating coupler cell; please check the script carefully.')
if not cell_gcB:
    raise Exception ('Cannot load grating coupler cell; please check the script carefully.')
if not cell_terminator:
    raise Exception ('Cannot load terminator cell; please check the script carefully.')
if not cell_laser:
    raise Exception ('Cannot load laser cell; please check the script carefully.')
#if not cell_pad:
#    raise Exception ('Cannot load bond pad cell; please check the script carefully.')
if not cell_waveguide:
    raise Exception ('Cannot load Waveguide Straight cell; please check the script carefully.')

# Waveguide type:
waveguides = ly.load_Waveguide_types()
waveguide1 = [w for w in waveguides if w['name']==waveguide_type]
if type(waveguide1) == type([]) and len(waveguide1)>0:
    waveguide = waveguide1[0]
else:
    waveguide = waveguides[0]
    print('error: waveguide type not found in PDK waveguides')
    raise Exception('error: waveguide type (%s) not found in PDK waveguides: \n%s' % (waveguide_type, [w['name'] for w in waveguides]))
radius_um = float(waveguide['radius'])
radius = to_itype(waveguide['radius'],ly.dbu)



# laser_height = cell_laser.bbox().height()
laser_dy = die_size / (n_lasers+1) # spread out evenly
laser_y = -die_size/2 #  


for row in range(0, n_lasers):
    
    # laser, place at absolute position
    laser_x = -die_edge + cell_laser.bbox().top + 150000 + 300e3
    laser_y += laser_dy
    t = pya.Trans.from_s('r0 %s,%s' % (int(laser_x), int(laser_y)) )
    inst_laser = top_cell.insert(pya.CellInstArray(cell_laser.cell_index(), t))
    
    # splitter tree
    from SiEPIC.utils.layout import y_splitter_tree
    if tree_depth == 4:
        n_x_gc_arrays = 6
        n_y_gc_arrays = 1
        x_tree_offset = 0
        inst_tree_in, inst_tree_out, cell_tree = y_splitter_tree(top_cell, tree_depth=tree_depth, y_splitter_cell=cell_y, library="SiEPICfab_Shuksan_PDK", wg_type=waveguide_type, draw_waveguides=True)
        ytree_x = inst_laser.bbox().right + x_tree_offset
        ytree_y = inst_laser.pinPoint('opt1').y # - cell_tree.bbox().height()/2
        t = Trans(Trans.R0, ytree_x, ytree_y)
        top_cell.insert(CellInstArray(cell_tree.cell_index(), t))
    else:
        # Handle other cases if needed
        raise Exception("Invalid tree_depth value")
    
    
    # Waveguide, laser to tree:
    connect_pins_with_waveguide(inst_laser, 'opt1', inst_tree_in, 'opt1', waveguide_type=waveguide_type, turtle_A=[10,90]) #turtle_B=[10,-90, 100, 90])

    '''
    # Grating couplers
    x_gc_array = -430e3 + x_tree_offset
    x_gc_array = inst_tree_out[0].pinPoint('opt2').x + 100e3
    y_gc_array = ytree_y - 934e3 / 2
       
    n_gcs_eacharray = 8
    dx_gc_arrays = 495e3
    dy_gc_arrays = 950e3+60e3
    dx_gcA_B = 0e3
    dy_gcA_B = 0e3
    
    import numpy as np
    inst_gcA = [[ [0] * n_x_gc_arrays for i in range(n_y_gc_arrays)] for j in range(n_gcs_eacharray) ]
    pointers_designs = []  # location for where the designs should go
    for k in range(0,n_x_gc_arrays):
        for j in range(0,n_y_gc_arrays):
            if k==n_x_gc_arrays-1 and j>1:
                continue
            for i in range(n_gcs_eacharray):
                # Grating couplers:
                t = Trans(Trans.R180, x_gc_array+k*dx_gc_arrays, y_gc_array+i*dy_gcs+j*dy_gc_arrays)
                inst_gcA[i][j][k] = cell.insert(CellInstArray(cell_gcA.cell_index(), t))
                
                if i in [1,2,3,4,5,6]:
                    inst_w = connect_cell(inst_gcA[i][j][k], 'opt1', cell_waveguide, 'opt1', relaxed_pinnames=True)#taper instead of y-branch
                    inst_w.transform(Trans(-10000,0))
                    if k==0 and j==0 and i==1:
                        cell_wg_gc = ly.create_cell('wg_gc')
                        connect_pins_with_waveguide(inst_w, 'opt1', inst_gcA[i][j][k], 'opt1', waveguide_type=waveguide_type, relaxed_pinnames=True).parent_cell=cell_wg_gc
                    cell.insert(CellInstArray(cell_wg_gc.cell_index(), 
                        Trans(Trans.R0, k*dx_gc_arrays,j*dy_gc_arrays+(i-1)*dy_gcs )))                
                if i in [1,3,5]:
                  pointers_designs.append([inst_w])

                #Automated test labels for the devices
                if i in [2,4,6]:
                     l = (i // 2) - 1  
                     t = Trans(Trans.R0, x_gc_array+k*dx_gc_arrays, y_gc_array+i*dy_gcs+j*dy_gc_arrays)
                     text = Text ('opt_in_TE_1310_device_%s_%s_%s' %(l+1,k+1,j+1), t)
                     shape = cell.shapes(ly.layer(TECHNOLOGY['Text'])).insert(text)
                     shape.text_size = 10/ly.dbu
                     shape.text_halign = 2
                
            # Waveguides for loopback:
            if k==0 and j==0:
                cell_wg_loopback = ly.create_cell('wg_loopback')
                #inst_wg_loopbackB = connect_pins_with_waveguide(inst_gcB[0][j][k], 'opt1', inst_gcB[n_gcs_eacharray-1][j][k], 'opt1', waveguide_type=waveguide_type, turtle_A=[10,-90,radius_um*2,-90,60,-90], turtle_B=[10,-90,radius_um*2,-90,60,-90], relaxed_pinnames=True)
                inst_wg_loopbackA = connect_pins_with_waveguide(inst_gcA[0][j][k], 'opt1', inst_gcA[n_gcs_eacharray-1][j][k], 'opt1', waveguide_type=waveguide_type, turtle_A=[10,90,radius_um*2,90,60+dx_gcA_B*ly.dbu+radius_um,90], turtle_B=[10,-90,radius_um*2,-90,60+dx_gcA_B*ly.dbu+radius_um,-90], relaxed_pinnames=True)
                #inst_wg_loopbackB.parent_cell=cell_wg_loopback
                inst_wg_loopbackA.parent_cell=cell_wg_loopback
            inst_wg_loopback = cell.insert(CellInstArray(cell_wg_loopback.cell_index(), 
                Trans(Trans.R0, k*dx_gc_arrays,j*dy_gc_arrays )))
    
            t = Trans(Trans.R0, x_gc_array+k*dx_gc_arrays, y_gc_array+i*dy_gcs+j*dy_gc_arrays)
            # Automated test labels:
            text = Text ('opt_in_TE_1310_device_%s_%s' %(k+1,j+1), t)
            shape = cell.shapes(ly.layer(TECHNOLOGY['Text'])).insert(text)
            shape.text_size = 10/ly.dbu
            shape.text_halign = 2
    '''      
  
  


# Origins for the layouts
x,y = 2.5e6,cell_Height+cell_Gap_Height

def disable_libraries():
    print('Disabling KLayout libraries')
    for l in pya.Library().library_ids():
        print(' - %s' % pya.Library().library_by_id(l).name())
        pya.Library().library_by_id(l).delete()
def enable_libraries():
    import siepicfab_ebeam_zep
    from importlib import reload  
    siepicfab_ebeam_zep = reload(siepicfab_ebeam_zep)
    siepicfab_ebeam_zep.pymacros = reload(siepicfab_ebeam_zep.pymacros)

disable_libraries()

design_count = 0
import subprocess
import pandas as pd
for f in [f for f in files_in if '.oas' in f.lower() or '.gds' in f.lower()]:
    basefilename = os.path.basename(f)

    # GitHub Action gets the actual time committed.  This can be done locally
    # via git restore-mtime.  Then we can load the time from the file stamp

    filedate = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y%m%d_%H%M")
    log("\nLoading: %s, dated %s" % (os.path.basename(f), filedate))

    # Tried to get it from GitHub but that didn't work:
    # get the time the file was last updated from the Git repository 
    # a = subprocess.run(['git', '-C', os.path.dirname(f), 'log', '-1', '--pretty=%ci',  basefilename], stdout = subprocess.PIPE) 
    # filedate = pd.to_datetime(str(a.stdout.decode("utf-8"))).strftime("%Y%m%d_%H%M")
    #filedate = os.path.getctime(os.path.dirname(f)) # .strftime("%Y%m%d_%H%M")
    
  
    # Load layout  
    layout2 = pya.Layout()
    layout2.read(f)

    if 'ebeam' in basefilename.lower():
        course = 'edXphot1x'
    elif 'elec413' in basefilename.lower():
        course = 'ELEC413'
    elif 'openebl' in basefilename.lower():
        course = 'openEBL'
    elif 'siepic_passives' in basefilename.lower():
        course = 'SiEPIC_Passives'
    else:
        course = 'openEBL'

    cell_course = eval('cell_' + course)
    log("  - course name: %s" % (course) )

    # Check the DBU Database Unit, in case someone changed it, e.g., 5 nm, or 0.1 nm.
    if round(layout2.dbu,10) != dbu:
        log('  - WARNING: The database unit (%s dbu) in the layout does not match the required dbu of %s.' % (layout2.dbu, dbu))
        print('  - WARNING: The database unit (%s dbu) in the layout does not match the required dbu of %s.' % (layout2.dbu, dbu))
        # Step 1: change the DBU to match, but that magnifies the layout
        wrong_dbu = layout2.dbu
        layout2.dbu = dbu
        # Step 2: scale the layout
        try:
            # determine the scaling required
            scaling = round(wrong_dbu / dbu, 10)
            layout2.transform (pya.ICplxTrans(scaling, 0, False, 0, 0))
            log('  - WARNING: Database resolution has been corrected and the layout scaled by %s' % scaling) 
        except:
            print('ERROR IN EBeam_merge.py: Incorrect DBU and scaling unsuccessful')
    
    # check that there is one top cell in the layout
    num_top_cells = len(layout2.top_cells())
    if num_top_cells > 1:
        log('  - layout should only contain one top cell; contains (%s): %s' % (num_top_cells, [c.name for c in layout2.top_cells()]) )
    if num_top_cells == 0:
        log('  - layout does not contain a top cell')

    # Find the top cell
    for cell in layout2.top_cells():
        if framework_file in os.path.basename(f) :
            # Create sub-cell using the filename under top cell
            subcell2 = layout.create_cell(os.path.basename(f)+"_"+filedate)
            t = Trans(Trans.R0, 0,0)
            top_cell.insert(CellInstArray(subcell2.cell_index(), t))
            # copy
            subcell2.copy_tree(layout2.cell(cell.name)) 
            break

        if os.path.basename(f) == ubc_file:
            # Create sub-cell using the filename under top cell
            subcell2 = layout.create_cell(os.path.basename(f)+"_"+filedate)
            t = Trans(Trans.R0, 8780000,8780000)      
            top_cell.insert(CellInstArray(subcell2.cell_index(), t))
            # copy
            subcell2.copy_tree(layout2.cell(cell.name)) 
            break


        if num_top_cells == 1 or cell.name.lower() == 'top' or cell.name.lower() == 'EBeam_':
            log("  - top cell: %s" % cell.name)

            # check layout height
            if cell.bbox().top < cell.bbox().bottom:
                log(' - WARNING: empty layout. Skipping.')
                break
                
            # Create sub-cell using the filename under course cell
            subcell2 = layout.create_cell(os.path.basename(f)+"_"+filedate)
            t = Trans(Trans.R0, x,y)
            cell_course.insert(CellInstArray(subcell2.cell_index(), t))
            
            # Clear extra layers
            layers_keep2 = [layer_SEM] if course in layer_SEM_allow else []
            for li in layout2.layer_infos():
                if li.to_s() in layers_keep + layers_keep2:
                    log('  - loading layer: %s' % li.to_s())
                else:
                    log('  - deleting layer: %s' % li.to_s())
                    layer_index = layout2.find_layer(li)
                    layout2.delete_layer(layer_index)
                    
            # Delete non-text geometries in the Text layer
            layer_index = layout2.find_layer(int(layer_text.split('/')[0]), int(layer_text.split('/')[1]))
            if type(layer_index) != type(None):
                s = cell.begin_shapes_rec(layer_index)
                shapes_to_delete = []
                while not s.at_end():
                    if s.shape().is_text():
                        text = s.shape().text.string
                        if text.startswith('SiEPIC-Tools'):
                            if log_siepictools:
                                log('  - %s' % s.shape() )
                            s.shape().delete()
                            subcell2.shapes(layerTextN).insert(pya.Text(text, 0, 0))
                        elif text.startswith('opt_in'):
                            log('  - measurement label: %s' % text )
                    else:
                        shapes_to_delete.append( s.shape() )
                    s.next()
                for s in shapes_to_delete:
                    s.delete()

            # bounding box of the cell
            bbox = cell.bbox()
            log('  - bounding box: %s' % bbox.to_s() )
                            
            # Create sub-cell under subcell cell, using user's cell name
            subcell = layout.create_cell(cell.name)
            t = Trans(Trans.R0, -bbox.left,-bbox.bottom)
            subcell_inst = subcell2.insert(CellInstArray(subcell.cell_index(), t))
        
            # clip cells
            cell2 = layout2.clip(cell.cell_index(), pya.Box(bbox.left,bbox.bottom,bbox.left+cell_Width,bbox.bottom+cell_Height))
            bbox2 = layout2.cell(cell2).bbox()
            if bbox != bbox2:
                log('  - WARNING: Cell was clipped to maximum size of %s X %s' % (cell_Width, cell_Height) )
                log('  - clipped bounding box: %s' % bbox2.to_s() )

            # copy
            subcell.copy_tree(layout2.cell(cell2))  
            
            log('  - Placed at position: %s, %s' % (x,y) )
            
            # connect to the laser tree    
            #x_out = inst_tree_out[0].pinPoint('opt2').x + 100e3
            # y_out = ytree_y - 934e3 / 2
            
            # intput waveguide:
            #x_in = bbox2.left - 10e3
            #y_in = bbox2.bottom + 10e3
            
            connect_pins_with_waveguide(inst_tree_out[design_count], 'opt2', subcell_inst, 'opt1', waveguide_type=waveguide_type) #, turtle_A=[10,90]) #turtle_B=[10,-90, 100, 90])

            design_count += 1
                
            # Measure the height of the cell that was added, and move up
            y += max (cell_Height, subcell.bbox().height()) + cell_Gap_Height
            # move right and bottom when we reach the top of the chip
            if y + cell_Height > chip_Height1 and x == 0:
                y = cell_Height + cell_Gap_Height
                x += cell_Width + cell_Gap_Width
            if y + cell_Height > chip_Height2:
                y = cell_Height + cell_Gap_Height
                x += cell_Width + cell_Gap_Width
            # check top right cutout for PCM
            if x + cell_Width > tr_cutout_x and y + cell_Height > tr_cutout_y:
                # go to the next column
                y = cell_Height + cell_Gap_Height    
                x += cell_Width + cell_Gap_Width
            # Check bottom right cutout for PCM
            if x + cell_Width > br_cutout_x and y < br_cutout_y:
                y = br_cutout_y
            # Check bottom right cutout #2 for PCM
            if x + cell_Width > br_cutout2_x and y < br_cutout2_y:
                y = br_cutout2_y

enable_libraries()



  

# Export for fabrication
import os 
path = os.path.dirname(os.path.realpath(__file__))
filename = top_cell_name
file_out = export_layout(top_cell, path, filename, relative_path = '.', format='oas', screenshot=True)


from SiEPIC._globals import Python_Env
if Python_Env == "Script":
    from SiEPIC.utils import klive
    klive.show(file_out, technology=tech)


# print('Completed %s designs' % n_designs)
