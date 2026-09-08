import pyvista as pv
import numpy as np
import os

 
def load_sim(path, start=0, num_epochs=1234, print_cam_pos=False):
    frames_path = path+"/frames"
    

    #Load starting frame
    def load_epoch(epoch):
        data = np.load(os.path.join(frames_path, f'epoch_{epoch}.npz'))
        return data['coords'], data['colors']

    coords, colors = load_epoch(start)

    plotter = pv.Plotter()
    plotter.set_background('black')

    cloud = pv.PolyData(coords)
    cloud.point_data['colors'] = colors
    actor = plotter.add_mesh(cloud, scalars='colors', rgb=True,
                         point_size=10, render_points_as_spheres=True)
    plotter.reset_camera()

    def update_epoch(value):
        epoch = int(value)
        coords, colors = load_epoch(epoch)
        new_cloud = pv.PolyData(coords)
        new_cloud.point_data['colors'] = colors
        actor.mapper.dataset.copy_from(new_cloud)
        plotter.render()

    slider = plotter.add_slider_widget(update_epoch,
                                   rng=[0, num_epochs - 1],
                                   value=start, title='Epoch', color='white')  
    plotter.show()

    if(print_cam_pos):
        print(plotter.camera_position)





def main():
    load_sim("/Users/ashnagibbons/Documents/CMP487/Spr2026_archive/rotorin3D", start=50)

if __name__ == "__main__":
    main()