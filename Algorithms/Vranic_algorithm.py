import numpy as np
import h5py
from shutil import copyfile
import read_hdf_file
import random
import math

class Segment:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def is_in_segment(self, value):
        if value >=self.start and value <= self.end:
            return True
        else:
            return False


class Momentum_cell:

    def __init__(self):
        self.segment_x = 0.
        self.segment_y = 0.
        self.segment_z = 0.

        self.momentums = []

    def get_idixes(self):
        self.momentums = np.array(self.momentums)
        indexes = np.array(self.momentums[:,3], dtype=('int'))
        return indexes


def create_sorted_momentum_list(data):
    
    size = len(data)
    indexes = [i for i in range(len(data))]
    result = []
    for i in range(0, size):
        result.append([data[i][3], data[i][4], data[i][5], indexes[i]])

    sort_list = sorted(result, key=lambda e: (e[0], e[1], e[2]))

    return sort_list


def get_segment(momentum_min, idx, step):
    start = momentum_min + (idx - 1) * step
    end = momentum_min + (idx) * step
    segment = Segment(start, end)
    return segment


def get_position_idx3d(x_patch, y_patch, z_patch, size_y, size_z):
    return (x_patch * size_y + y_patch) * size_z + z_patch


def get_cell_idx(max_coord, min_coord, separator, x_current):
    """ Get name of particles group """
    lenght = max_coord - min_coord
    return max(0, min(int((x_current - min_coord) * separator / lenght), separator - 1))


def create_momentum_cells(sorted_momentum_list, tolerance_momentum, segment_x, segment_y, segment_z):

    x_momentum_min = segment_x.start
    x_momentum_max = segment_x.end

    y_momentum_min = segment_y.start
    y_momentum_max = segment_y.end

    z_momentum_min = segment_z.start
    z_momentum_max = segment_z.end

    num_x_steps = int((x_momentum_max - x_momentum_min)/ tolerance_momentum) + 1
    num_y_steps = int((y_momentum_max - y_momentum_min) / tolerance_momentum) + 1
    num_z_steps = int((z_momentum_max - z_momentum_min) / tolerance_momentum) + 1

    size_cells = num_x_steps * num_y_steps * num_z_steps
    cells = [Momentum_cell() for i in range(size_cells)]

    for i in range(0, len(sorted_momentum_list)):
        x_idx = get_cell_idx(x_momentum_max, x_momentum_min, num_x_steps, sorted_momentum_list[i][0])

        y_idx = get_cell_idx(y_momentum_max, y_momentum_min, num_y_steps, sorted_momentum_list[i][1])
        z_idx = get_cell_idx(z_momentum_max, z_momentum_min, num_z_steps, sorted_momentum_list[i][2])

        current_idx = get_position_idx3d(x_idx, y_idx, z_idx, num_y_steps, num_z_steps)
        cells[current_idx].momentums.append(sorted_momentum_list[i])

    return cells


def get_start_ranges(data):

    x_min = min(data[:,3])
    x_max = max(data[:,3])

    x_segment = Segment(x_min, x_max)

    y_min = min(data[:,4])
    y_max = max(data[:,4])

    y_segment = Segment(y_min, y_max)

    z_min = min(data[:,5])
    z_max = max(data[:,5])

    z_segment = Segment(z_min, z_max)

    return x_segment, y_segment, z_segment


def get_energy_value(momentum, mass):

    c = 299792458.
    momentum_norm = [momentum[0]/(mass * c), momentum[1]/(mass * c), momentum[2]/(mass * c) ]
    norm_vector = momentum_norm[0] * momentum_norm[0] + momentum_norm[1] * momentum_norm[1] + momentum_norm[2] * momentum_norm[2]
    energy = norm_vector * c * c +(mass * c * c) * (mass * c * c)
    result = math.sqrt(energy)
    result = result/(mass * c * c)
    return result


def get_energy_value_masless(momentum):

    c = 299792458.
    momentum_norm = [momentum[0]/c, momentum[1]/c, momentum[2]/c ]
    norm_vector = momentum_norm[0] * momentum_norm[0] + momentum_norm[1] * momentum_norm[1] + momentum_norm[2] * momentum_norm[2]
    energy = norm_vector * c * c
    result = math.sqrt(energy)
    result = result/( c * c)
    return result


def get_weighted_momentum(momentums, weights):

    values_x = 0.
    values_y = 0.
    values_z = 0.

    for i in range(0, len(momentums)):
        values_x += momentums[i][0] * weights[i]
        values_y += momentums[i][1] * weights[i]
        values_z += momentums[i][2] * weights[i]

    result = [values_x, values_y, values_z]
    return result


def get_weighted_energy(momentums, weights, mass):

    sum_energy = []

    for i in range(0, len(momentums)):
        energy = get_energy_value(momentums[i], mass)
        sum_energy.append(energy * weights[i])

    result_sum_energy = sum(sum_energy)

    return result_sum_energy


def get_weighted_energy_massless(momentums, weights):

    sum_energy = []

    for i in range(0, len(momentums)):
        energy = get_energy_value_masless(momentums[i])
        sum_energy.append(energy * weights[i])

    result_sum_energy = sum(sum_energy)

    return result_sum_energy


def get_momentum_vector_lenght(energy_t):

    return math.sqrt(energy_t * energy_t  - 1.)


def get_cos_phi(start_momentum_vector, value_momentum_end, sum_weight):

    len_start_vector = \
        math.sqrt(start_momentum_vector[0] * start_momentum_vector[0] +
                  start_momentum_vector[1] * start_momentum_vector[1]
                  + start_momentum_vector[2] * start_momentum_vector[2])

    result = len_start_vector/(value_momentum_end * sum_weight)

    return result


def get_angle_phi(momentums, mass, weights):
    sum_weights = sum(weights)

    momentum_vector_t = get_weighted_momentum(momentums, weights)

    energy_t = get_weighted_energy(momentums, weights, mass)
    energy_t = energy_t / sum_weights
    norm_vector = get_momentum_vector_lenght(energy_t)
    cos_phi = get_cos_phi(momentum_vector_t, norm_vector, sum_weights)
    return math.acos(cos_phi)


def get_angle_phi_massles(momentums, weights):
    sum_weights = sum(weights)

    momentum_vector_t = get_weighted_momentum(momentums, weights)

    energy_t = get_weighted_energy(momentums, weights)
    energy_t = energy_t / sum_weights
    norm_vector = get_momentum_vector_lenght(energy_t)
    cos_phi = get_cos_phi(momentum_vector_t, norm_vector, sum_weights)
    return math.acos(cos_phi)


def get_angle_alpha(momentums):

    lenght_vector = math.sqrt(
        momentums[0] * momentums[0] + momentums[1] * momentums[1] + momentums[2] * momentums[2])
    plane_vector = math.sqrt(
        momentums[0] * momentums[0] + momentums[1] * momentums[1])
    return math.acos(plane_vector/lenght_vector)


def get_vector_p_a(momentums, phi, alpha):

    lenght_vector = math.sqrt(
        momentums[0] * momentums[0] + momentums[1] * momentums[1] + momentums[2] * momentums[2])
    x_value = lenght_vector * math.cos(phi)
    y_value = lenght_vector * math.sin(phi)
    z_value = lenght_vector * math.cos(alpha)
    p_a = [x_value, y_value, z_value]

    return p_a


def get_vector_p_b(momentums, phi, alpha):
    lenght_vector = math.sqrt(
        momentums[0] * momentums[0] + momentums[1] * momentums[1] + momentums[2] * momentums[2])
    x_value = lenght_vector * math.sin(phi)
    y_value = lenght_vector * math.cos(phi)
    z_value = lenght_vector * math.cos(alpha)
    p_b = [x_value, y_value, z_value]

    return p_b


def recalculate_momentum(momentums, weights, type_particles, mass):

    if type_particles == 'massless':
        alpha = get_angle_alpha(momentums)

        momentum_vector_t = get_weighted_momentum(momentums, weights)
        phi = get_angle_phi_massles(momentums, weights)

        first_point = get_vector_p_a(momentum_vector_t, phi, alpha)
        second_point = get_vector_p_b(momentum_vector_t, phi, alpha)
        return first_point, second_point

    if type_particles == 'mass':

        momentum_vector_t = get_weighted_momentum(momentums, weights)
        phi = get_angle_phi(momentums, mass, weights)
        alpha = get_angle_alpha(momentum_vector_t)

        first_point = get_vector_p_a(momentum_vector_t, phi, alpha)
        second_point = get_vector_p_b(momentum_vector_t, phi, alpha)

        return first_point, second_point


def calculate_result_points(data, weights, idxes_array):
    first_point = []
    second_point = []
    sum_weights = sum(weights)
    result_weight = [sum_weights / 2., sum_weights / 2.]

    idxes_array.sort()

    idexes_coordinates = random.sample(idxes_array.data, 2)
    first_coordinates = data[idexes_coordinates[0]]
    second_coordinates = data[idexes_coordinates[1]]
    first_point.append(first_coordinates[0:3])
    second_point.append(second_coordinates[0:3])

    return first_coordinates, second_coordinates, result_weight


def merge_into_points(first_coordinates, second_coordinates, first_momentum, second_momentum):
    first_point = [first_coordinates[0], first_coordinates[1], first_coordinates[2],  first_momentum[0], first_momentum[1], first_momentum[2]]
    second_point = [second_coordinates[0], second_coordinates[1], second_coordinates[2], second_momentum[0],
                    second_momentum[1], second_momentum[2]]

    return first_point, second_point


def recount_cells(data, weights, momentum_cells, mass):
    result = []
    weights_result = []

    type_particles = ''
    if mass == 0:
        type_particles = 'massless'
    else:
        type_particles = 'mass'

    for i in range(0, len(momentum_cells)):
        if len(momentum_cells[i].momentums) != 0:
            idxes_array = momentum_cells[i].get_idixes()
            if len(idxes_array) > 1:
                first_coordinates, second_coordinates, result_weight = calculate_result_points(data, weights[idxes_array], idxes_array)
                first_momentum, second_momentum = recalculate_momentum(momentum_cells[i].momentums, weights[idxes_array], type_particles, mass)
                first_point, second_point = merge_into_points(first_coordinates, second_coordinates, first_momentum, second_momentum)
                result.append(first_point)
                result.append(second_point)
                weights_result.append(result_weight[0])
                weights_result.append(result_weight[1])

            else:
                result.append(data[idxes_array])
                weights_result.append(weights[idxes_array])

    return result, weights_result


class Vranic_merging_algorithm_parameters:
    """Tolerance is array-like, first -- coordinate tolerance, second -- momentum tolerance"""

    def __init__(self, tolerance_momentum, dimension, type_particles):
        self.tolerance_momentum = tolerance_momentum
        self.dimension = dimension
        self.type_particles = type_particles


class Vranic_merging_algorithm:
    """Main algorithm. Parameters is VoronoiMergingAlgorithmParameters """

    def __init__(self, parameters):
        self.parameters = parameters
        self.dimensions = None

    def _run(self, data, weigths, mass):
        data = np.array(data)
        weigths = np.array(weigths)
        x_segment, y_segment, z_segment = get_start_ranges(data)

        sorted_momentum = create_sorted_momentum_list(data)
        cells = create_momentum_cells(sorted_momentum, self.parameters.tolerance_momentum, x_segment, y_segment, z_segment)
        data, weights = recount_cells(data, weigths, cells, mass)
        return data, weights





if __name__ == "__main__":
   hdf_file_name = '/home/kseniia/Documents/k_means_measure/data00000355.h5'
   hdf_file_reduction_name = '/home/kseniia/Documents/k_means_measure/data00000355_thinning.h5'
   copyfile(hdf_file_name, hdf_file_reduction_name)
   hdf_file = h5py.File(hdf_file_name, 'a')
   hdf_file_reduction = h5py.File(hdf_file_reduction_name, 'a')
   particles_name = read_hdf_file.get_particles_name(hdf_file_reduction)
   particles_collect = read_hdf_file.ParticlesGroups(particles_name)
   hdf_file.visititems(particles_collect)
   tolerance_parsent = 1.9e-23

   dimension = 3
   type_particles ='mass'

   parameters = Vranic_merging_algorithm_parameters(tolerance_parsent, dimension, type_particles)
   group = particles_collect.particles_groups[0]
   for group in particles_collect.particles_groups:
       data, weights, dimensions\
           = read_hdf_file.read_points_group(group)
       algorithm = Vranic_merging_algorithm(parameters)
       data = np.array(data)
       mass = 9.10938291E-31
       algorithm._run(data, weights, mass)




