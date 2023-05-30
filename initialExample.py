import polyscope as ps
import numpy as np
import functions
import marching_squares as ms
import sys # for printing max


# todo
# - implement linear interpolation for the marching squares cut
# - implement the marching squares situation in which there is two cuts in one square
# - improve marching squares performance
#
# - implement smooth version of math functions for Boolean operations (+ research)
# - fully implement batman function
# - currently I'm just using any implicit functions -> use signed distance functions
#
# - visualize SDF (function/distance) values
# - mesh coloring with LERP
# - use vectors for x y coordinates
#
# project isonlines to bottom plane instead of current one


# some options
ps.set_program_name("initial polyscope test")
ps.set_verbosity(0)
ps.set_use_prefs_file(False)
ps.set_up_dir("z_up") 

# Initialize polyscope, creating graphics contexts and constructing a window.
# Should be called exactly once.
ps.init()





# create coordinate axis
axis_len = 1;
x_axis_nodes = np.array([[0,0,0], [axis_len,0,0]])
x_axis_edges = np.array([[0,1]])
x_axis_curve = ps.register_curve_network("x_axis", x_axis_nodes, x_axis_edges)

y_axis_nodes = np.array([[0,0,0], [0,axis_len,0]])
y_axis_edges = np.array([[0,1]])
y_axis_curve = ps.register_curve_network("y_axis", y_axis_nodes, y_axis_edges)

z_axis_nodes = np.array([[0,0,0], [0,0,axis_len]])
z_axis_edges = np.array([[0,1]])
z_axis_curve = ps.register_curve_network("z_axis", z_axis_nodes, z_axis_edges)







# create the grid to discretely evaluate the function on

# specifies in which 2D domain input should be sampled
x_range = np.arange(-2,2, 0.01)
y_range = np.arange(-2,2, 0.01)

# grid: [x_position, y_position, function_value]
vertice_grid_shape = (x_range.size, y_range.size, 3)
vertice_grid = np.ndarray(vertice_grid_shape)
# set initial coordinates and values for the grid
for i in range(vertice_grid_shape[0]):
    for j in range(vertice_grid_shape[1]):
        vertice_grid[i,j,0] = x_range[i] # set x coordinate
        vertice_grid[i,j,1] = y_range[j] # set y coordinate
        vertice_grid[i,j,2] = 100 # set initial value


# use marching squares on a function
#test_square_grid = ms.MS_Grid(vertice_grid, 0, functions.unit_circle)



unit_circle = functions.circle_function(0,0,1)
shifted_unit_circle = functions.circle_function(0, 0.7, 1.25)
#squares_circles_subtract = ms.MS_Grid(vertice_grid, 0, functions.subtract(unit_circle, shifted_unit_circle))

unit_circle_SDF = functions.circle_SDF(0,0,1)
shifted_unit_circle_SDF = functions.circle_SDF(0, 0.7, 1.25)
#squares_circles_subtract = ms.MS_Grid(vertice_grid, 0, functions.subtract(unit_circle_SDF, shifted_unit_circle_SDF))
#squares_circles_union = ms.MS_Grid(vertice_grid, 0, functions.union(unit_circle_SDF, shifted_unit_circle_SDF))
squares_circles_intersection = ms.MS_Grid(vertice_grid, 0, functions.intersection(unit_circle_SDF, shifted_unit_circle_SDF))





#shape_points, shape_edges = squares_circles_intersection.full_run()
#shape_points, shape_edges = squares_circles_subtract.full_run()
#shape_points, shape_edges = squares_circles_union.full_run()
#shape = ps.register_curve_network("circles_subtract", shape_points, shape_edges)

rectangle = functions.rectangle_function(0,0,1,1)
#squares_rectangle = ms.MS_Grid(vertice_grid,0,rectangle)
squares_rectangle = ms.MS_Grid(vertice_grid,0,functions.subtract(rectangle, shifted_unit_circle_SDF))

rectangle_points, rectangle_edges = squares_rectangle.full_run()
shape_rectangle = ps.register_curve_network("rectangle", rectangle_points, rectangle_edges)

"""
# visualizing functions values on z axis, as vectors
#value_vectors = np.ndarray((vertice_grid.shape[0]*vertice_grid.shape[1], 3))
value_vectors_points = []
value_vectors_edges = []
value_vectors_edge_colors = []
point_index_counter = 0
edge_index_counter = 0
for i in range(0,vertice_grid_shape[0],25):
    for j in range(0,vertice_grid_shape[1], 25):
        # vertice_grid[i,j,2] = 100 should have the correct value still from ms squares
        base = np.asarray([vertice_grid[i,j,0], vertice_grid[i,j,1], 0]) # the coordinate
        top = np.asarray([vertice_grid[i,j,0], vertice_grid[i,j,1], vertice_grid[i,j,2]])
        value_vectors_points.append(base)
        value_vectors_points.append(top)
        value_vectors_edges.append(np.asarray([point_index_counter, point_index_counter+1]))

        # value <= 0 blue, else red
        if (vertice_grid[i,j,2] <= 0): 
            value_vectors_edge_colors.append(np.asarray([0,0,1]))
        else:
            value_vectors_edge_colors.append(np.asarray([1,0,0]))
        point_index_counter += 2
value_vectors_points = np.asarray(value_vectors_points)
value_vectors_edges = np.asarray(value_vectors_edges)
value_vectors_edge_colors = np.asarray(value_vectors_edge_colors)
value_net = ps.register_curve_network("my_value_vectors", value_vectors_points, value_vectors_edges, transparency=0.3)
value_net.add_color_quantity("my_value_colors", value_vectors_edge_colors, defined_on="edges", enabled=True)
"""

# visualizing functions values on z axis
# smaller steps -> more precision (less than 1 doesn't make sense, for that, the evaluation grid should be adjusted)
resolution_step = 5
mesh_grid_x = np.int64(np.ceil(vertice_grid.shape[0]/resolution_step))
mesh_grid_y = np.int64(np.ceil(vertice_grid.shape[1]/resolution_step))

number_mesh_points = mesh_grid_x*mesh_grid_y

number_x_edges = mesh_grid_x*(mesh_grid_y-1)
number_y_edges = (mesh_grid_x-1)*mesh_grid_y
number_diag_edges = (mesh_grid_x-1)*(mesh_grid_y-1)
number_total_edges = number_x_edges + number_y_edges + number_diag_edges

number_of_faces = (mesh_grid_x-1)*(mesh_grid_y-1)*2

value_mesh_points = np.ndarray((mesh_grid_x*mesh_grid_y, 3)) # flat array of 3D mesh points

value_mesh_edges = np.ndarray((number_total_edges, 2)) # flat array of edges (as length 2 array)

value_mesh_faces = np.ndarray((number_of_faces, 3)) # flat array of triangle (3 edges) faces

face_vertice_counter = 0
for i in range(mesh_grid_x): 
    for j in range(mesh_grid_y):
        # the points
        value_mesh_points[i*mesh_grid_y+j,:] = vertice_grid[i*resolution_step, j*resolution_step, :]

        # the edges and faces
        # face calculation is based on edges, one faces consists of the two edges of the diagonal and one x edge
        # may God have mercy on me for this index calculation

        # x direction edges for curves 
        if (j < mesh_grid_y-1):
            x_edge_index = i*(mesh_grid_y-1)+j
            value_mesh_edges[x_edge_index, :] = np.asarray([i*mesh_grid_y+j, i*mesh_grid_y+j+1])
            # the x point for mesh faces 
            if (i < mesh_grid_x-1):
                value_mesh_faces[i*(mesh_grid_y-1)+j, 2] = np.int64(value_mesh_edges[x_edge_index,1])
                value_mesh_faces[i*(mesh_grid_y-1)+j+number_of_faces//2, 2] = np.int64(value_mesh_edges[x_edge_index,0]+mesh_grid_x)

        # the y direction edges
        if (i < mesh_grid_x and (j != 0 or i==0) and i*(mesh_grid_y-1)+j+number_x_edges != number_x_edges+number_y_edges):
            y_edge_index = i*(mesh_grid_y-1)+j+number_x_edges
            value_mesh_edges[y_edge_index, :] = np.asarray([i*(mesh_grid_y-1)+j, (i+1)*mesh_grid_y+j-i])

        # the diagonal edges
        if (i >= mesh_grid_x-1 or j >= mesh_grid_y-1):
            continue
        else:
            diag_edge_index = i*(mesh_grid_y-1)+j+number_x_edges+number_y_edges
            value_mesh_edges[diag_edge_index,:] = np.asarray([i*mesh_grid_y+j, (i+1)*mesh_grid_y+j+1])

            # diagonal points for mesh faces
            # first half (left half of square)
            value_mesh_faces[i*(mesh_grid_y-1)+j, 0] = np.int64(value_mesh_edges[diag_edge_index,0])
            value_mesh_faces[i*(mesh_grid_y-1)+j, 1] = np.int64(value_mesh_edges[diag_edge_index,1])
            # right half
            value_mesh_faces[i*(mesh_grid_y-1)+j+number_of_faces//2, 0] = np.int64(value_mesh_edges[diag_edge_index,0])
            value_mesh_faces[i*(mesh_grid_y-1)+j+number_of_faces//2, 1] = np.int64(value_mesh_edges[diag_edge_index,1])


#value_curve_network = ps.register_curve_network("my_future_mesh", value_mesh_points, value_mesh_edges)  
value_mesh = ps.register_surface_mesh("my_value_mesh", value_mesh_points, value_mesh_faces)      
         
# coloring the mesh
# majority of point values determines color
# ideally with LERP
value_mesh_colors = np.ndarray((number_of_faces,3))
blue = np.asarray([0,0,1])
red = np.asarray([1,0,0])
for face in range (number_of_faces):
    positive_vertices = 0
    for vertice in range(3):
        this_vertice = value_mesh_faces[face,vertice]
        this_value = value_mesh_points[np.int64(this_vertice),2]
        if this_value > 0:
            positive_vertices += 1
    if positive_vertices >= 2:
        # color face red
        value_mesh_colors[face] = red
    else:
        # color face blue
        value_mesh_colors[face] = blue
value_mesh.add_color_quantity("value_mesh_colors", value_mesh_colors, defined_on='faces', enabled=True)
    



#value_mesh_points[i*mesh_grid_y+j,:] = vertice_grid[i*resolution_step, j*resolution_step, :]
                

        



print("total points: ", number_mesh_points)
print("total edges", number_total_edges)
print("x, ", number_x_edges)
print("y", number_y_edges)
print("diag" , number_diag_edges)
print("mesh x", mesh_grid_x)
print("mesh_y", mesh_grid_y)
print("resolution step of mesh: ", resolution_step)
print("number of mesh faces", number_of_faces)
print("-"*50)




"""

# coloring points based on whether the value is positive or negative
for i in range(0,vertice_grid_shape[0],25):
    for j in range(0,vertice_grid_shape[1], 25):
        # vertice_grid[i,j,2] = 100 should have the correct value still from ms squares
        base = np.asarray([vertice_grid[i,j,0], vertice_grid[i,j,1], 0]) # the coordinate
        top = np.asarray([vertice_grid[i,j,0], vertice_grid[i,j,1], vertice_grid[i,j,2]])
        value_vectors_points.append(base)
        value_vectors_points.append(top)
        value_vectors_edges.append(np.asarray([point_index_counter, point_index_counter+1]))

        # value <= 0 blue, else red
        if (vertice_grid[i,j,2] <= 0): 
            value_vectors_edge_colors.append(np.asarray([0,0,1]))
        else:
            value_vectors_edge_colors.append(np.asarray([1,0,0]))
        point_index_counter += 2
value_vectors_points = np.asarray(value_vectors_points)
value_vectors_edges = np.asarray(value_vectors_edges)
value_vectors_edge_colors = np.asarray(value_vectors_edge_colors)
value_net = ps.register_curve_network("my_value_vectors", value_vectors_points, value_vectors_edges, transparency=0.3)
value_net.add_color_quantity("my_value_colors", value_vectors_edge_colors, defined_on="edges", enabled=True)
        """


ps.show()