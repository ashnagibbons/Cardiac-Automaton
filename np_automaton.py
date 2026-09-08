from PIL import Image
import random
import math
import numpy as np
import cv2
import os


def initialize(percentFibril = .15, fibrilLength = 5, defaultRefractoryPeriod = 49, patchRefractoryPeriod = 53, \
               gridDimension1 = 576, gridDimension2 = 576, patchDim1 = 50, patchDim2= 20):

    #assign all variables
    percentFib = percentFibril
    fibLength = fibrilLength
    dRefracPer = defaultRefractoryPeriod
    pRefracPer = patchRefractoryPeriod
    rows = gridDimension1
    cols = gridDimension2

    #arrays: excitable, lastactivated, activatenext, refracPer
    excitable = np.ones((rows, cols), dtype=np.int64)
    refracPer = np.full((rows, cols), dRefracPer, dtype=np.int64)
    lastActivated = np.full((rows, cols), -9999, dtype=np.int64)
    activateNext = np.full((rows, cols), -9999, dtype=np.int64)
    
    
    #calculate number of fibrils 
    fibrosisCover = math.floor(rows*cols*percentFib)
    halfDist = fibLength//2
    numFibrils = math.floor(fibrosisCover/fibLength)

    #place horizontal and vertical fibers
    for i in range(numFibrils):
        fibCenterX = random.randint((halfDist-1), rows-(halfDist+1))

        fibCenterY = random.randint((halfDist-1), cols-(halfDist+1))

        hozOrVert = random.randint(0, 1)

        if (hozOrVert == 1):
            for i in range(fibLength):
                excitable[fibCenterX + i - halfDist, fibCenterY] = 0
        else:
            for i in range(fibLength):
                excitable[fibCenterX, fibCenterY+i - halfDist] = 0
        
    
    #place refrac patches
    refracPatch1 = input(f"""Please input the coordinates of the node at the top left corner of the {patchDim1}x{patchDim2} refractory\n
                         patch in the format x,y. Please note the patch must fit in the\n
                         matrix, so please do not input a row more than row {rows - patchDim1} or column {cols - patchDim2}.""")

    patch1x = int(refracPatch1.split(',')[0])
    patch1y = int(refracPatch1.split(',')[1])

    for i in range(patchDim1):
        for j in range(patchDim2):
            refracPer[patch1x + i, patch1y + j] = pRefracPer


    refracPatch2 = input(f"""Please do the same for the {patchDim2}x{patchDim1} refractory patch in the same format. \n
                         Limits are to row {rows - patchDim2} and column {cols - patchDim1}.""")

    patch2x = int(refracPatch2.split(',')[0])
    patch2y = int(refracPatch2.split(',')[1])

    for i in range(patchDim2):
        for j in range(patchDim1):
            refracPer[patch2x + i, patch2y + j] = pRefracPer

    # Clear fibrosis from patch regions
    excitable[patch1x:patch1x+patchDim1, patch1y:patch1y+patchDim2] = 1
    excitable[patch2x:patch2x+patchDim2, patch2y:patch2y+patchDim1] = 1

    path = input("Input the absolute path to the directory in which files for this instance will be saved.\n")

    os.makedirs(path, exist_ok=True)
    
    init_rgb = np.zeros((rows, cols, 3), dtype=np.uint8)
    init_rgb[excitable == 0] = [255, 0, 0]
    init_rgb[refracPer == pRefracPer] = [0, 255, 0]
    image = Image.fromarray(init_rgb)
    image.save(path + '/initial.png')

    return excitable, refracPer, lastActivated, activateNext, path

def read_color_palette(path): 
    #put your own path to the colorscale.txt file when you download it
    colorfile = open(path)
    colors = colorfile.readlines()
    rgb_colors = []

    for line in colors:
        rgb_line = [int(x) for x in line.split()]
        rgb_colors.append(rgb_line)

    return rgb_colors

 
def iter_epochs(excitable, refracPer, lastActivated, activateNext, path, color_palette_path, num_epochs = 1234, stimInt = 51, aniso = 'x', fps=10):

    #rows = excitable.shape[1]
    #cols = excitable.shape[0]

    color_matrix = np.array(read_color_palette(color_palette_path))
    os.mkdir(path+"/frames")

    init_coords = input("Please input the coordinates from where the stimulus will initiate in the form x,y: ")
    init_point_x = int(init_coords.split(',')[0])
    init_point_y= int(init_coords.split(',')[1])
    
    lastActivated[init_point_x, init_point_y] = 0
    activateNext[init_point_x, init_point_y] = 1
    
    for epoch in range(num_epochs):#this is equal to total runtime 2468 ms
      
        #iterate through the matrix to get the png of the epoch
        imgName = 'epoch' + str(epoch)
        img = Image.new('RGB', (excitable.shape[1], excitable.shape[0]), (0,0,0))
        

        timeSinceActivated = epoch - lastActivated
        color_idx = np.clip(1 + (timeSinceActivated * 998 // 500), 1, 999).astype(np.int64)

        color_idx[lastActivated == -9999] = 0
        color_idx[lastActivated == epoch + 1] = 0
        color_idx[excitable == 0] = 0

        pixels = color_matrix[color_idx]
        img = Image.fromarray(pixels.astype(np.uint8))
        
        img.save(path+"/frames/"+imgName+'.png')
        
        if epoch == stimInt:
            activateNext[init_point_x, init_point_y] = stimInt

        firing = (activateNext == epoch)

        lastActivated[firing] = epoch

        can_fire = (excitable == 1) & (epoch - lastActivated > refracPer)

        from_left  = np.roll(firing,  1, axis=1);  from_left[:,  0] = False
        from_right = np.roll(firing, -1, axis=1);  from_right[:,-1] = False
        from_above = np.roll(firing,  1, axis=0);  from_above[0, :] = False
        from_below = np.roll(firing, -1, axis=0);  from_below[-1,:] = False

        if aniso == 'x':
            activateNext[(from_left | from_right) & can_fire] = epoch + 2
            activateNext[(from_above | from_below) & can_fire] = epoch + 1
        elif aniso == 'y':
            activateNext[(from_above | from_below) & can_fire] = epoch + 2
            activateNext[(from_left | from_right) & can_fire] = epoch + 1
            
    
    image_folder = path+'/frames'
    video_name = path + '/video.avi' 

    images = sorted(
    [img for img in os.listdir(image_folder) if img.endswith(".png")],
    key=lambda x: int(x.replace('epoch', '').replace('.png', ''))
    )

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'MJPG'), fps, (width, height))

    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))

    cv2.destroyAllWindows()
    video.release()  



def main():
    excitable, refracPer, lastActivated, activateNext, path = initialize()
    iter_epochs(excitable, refracPer, lastActivated, activateNext, path, color_palette_path='/Users/ashnagibbons/Documents/CMP487/FinalFiles/colorscale.txt')

if __name__ == "__main__":
    main()


