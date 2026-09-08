import pyvista as pv
import numpy as np
import os
import cv2

def make_video(frames_path, output_path, num_epochs=1234, fps=10, cam_pos = [(329.2212816378437, 1222.438835370703, 854.361384406489), 
                                                                             (287.5, 287.5, 2.0), 
                                                                             (-0.5737259055555435, -0.5376782779834972, 0.6178516445548824)]):

    os.makedirs(output_path)
    # Set up offscreen plotter
    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
    plotter.set_background('black')

    # Load first frame to initialise the actor
    data = np.load(os.path.join(frames_path, 'epoch_0.npz'))
    coords, colors = data['coords'], data['colors']

    if len(coords) > 0:
        cloud = pv.PolyData(coords)
        cloud.point_data['colors'] = colors
        actor = plotter.add_mesh(cloud, scalars='colors', rgb=True,
                                 point_size=4, render_points_as_spheres=True)
    else:
        # Placeholder if epoch 0 is empty
        cloud = pv.PolyData(np.zeros((1, 3), dtype=np.float32))
        cloud.point_data['colors'] = np.zeros((1, 3), dtype=np.uint8)
        actor = plotter.add_mesh(cloud, scalars='colors', rgb=True,
                                 point_size=10, render_points_as_spheres=True)

    plotter.camera_position = cam_pos
    plotter.camera.clipping_range = (0.1, 100000)

    # Get frame size from a test screenshot
    test_img = plotter.screenshot(return_img=True)
    h, w = test_img.shape[:2]

    video_path = os.path.join(output_path, 'video.avi')
    writer = cv2.VideoWriter(video_path,
                             cv2.VideoWriter_fourcc(*'MJPG'),
                             fps, (w, h))

    for epoch in range(num_epochs):
        data = np.load(os.path.join(frames_path, f'epoch_{epoch}.npz'))
        coords = data['coords']
        colors = data['colors']

        # Update actor in-place — same approach as the slider viewer
        if len(coords) > 0:
            new_cloud = pv.PolyData(coords)
            new_cloud.point_data['colors'] = colors
        else:
            new_cloud = pv.PolyData(np.zeros((1, 3), dtype=np.float32))
            new_cloud.point_data['colors'] = np.zeros((1, 3), dtype=np.uint8)

        actor.mapper.dataset.copy_from(new_cloud)
        plotter.render()

        # Screenshot returns RGB, OpenCV needs BGR
        img = plotter.screenshot(return_img=True)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        writer.write(img_bgr)

        if epoch % 100 == 0:
            print(f'Rendered epoch {epoch}/{num_epochs}')

    writer.release()
    plotter.close()
    print(f'Video saved to {video_path}')

def main():
    make_video(frames_path="/Users/ashnagibbons/storedatatest/frames", 
            output_path="/Users/ashnagibbons/simvideo2", cam_pos=[(913.9099539705085, 1321.3222077766106, 903.3593531776534),
 (287.5, 319.5, 2.0),
 (-0.483979141718435, -0.39838610732799723, 0.7791358674002452)])
    
if __name__ == "__main__":
    main()
