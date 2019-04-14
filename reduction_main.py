from shutil import copyfile
import read_hdf_file
import argparse
import Voronoi_algorithm
import os
import h5py
import numpy
import Random_thinning_algorithm
import copy
import k_means_clustering_algorithm
import Vranic_algorithm
import Number_conservative_thinning_algorithm
import Leveling_thinning_algorithm
import Energy_conservative_thinning_algorithm
import k_means_merge_average_algorithm


class Algorithm:
    # Create based on class name:
    def factory(self, type, mass=1., reduction_percent=1., leveling_persent=1., dimensions=None, max_iterations=1., tolerance=1.):
        if type == "Random": return Random_thinning_algorithm.RandomThinningAlgorithm(reduction_percent)
        if type == "Number_conservative": return Number_conservative_thinning_algorithm.Number_conservative_thinning_algorithm(reduction_percent)
        if type == "Energy_conservative":
            return Energy_conservative_thinning_algorithm.Energy_conservative_thinning_algorithm(reduction_percent, dimensions, mass)
        if type == "kmeans":
            return k_means_clustering_algorithm.K_means_clustering_algorithm(reduction_percent, max_iterations, tolerance)
        if type == "kmeans-avg":
            return k_means_merge_average_algorithm.K_means_merge_average_algorithm(reduction_percent, max_iterations, tolerance)
        assert 0, "Bad type_algoritm: " + type
    factory = staticmethod(factory)


def new_base_function(hdf_file_name, hdf_file_reduction_name, type, parametrs):
    particles_collect, hdf_file_reduction = get_particles_groups(hdf_file_name, hdf_file_reduction_name)

    for group in particles_collect.particles_groups:
        one_type_particle(type, group, hdf_file_reduction)


def one_type_particle(type, group, hdf_file_reduction):
    algorithm = Algorithm.factory(type)
    thinning_base_procedure_v2(hdf_file_reduction, group, algorithm)


def thinning_base_procedure_v2(hdf_file_reduction, group, algorithm):

    data, weights, dimensions \
        = read_hdf_file.read_points_group(group)
    num_particles, num_particles_offset = read_hdf_file.read_patches_values(group)

    reduced_data, reduced_weights, result_num_particles = \
        iterate_patches(data, weights, num_particles_offset, algorithm)

    library_datasets = read_hdf_file.create_datasets_from_vector(reduced_data, dimensions)

    read_hdf_file.write_group_values(hdf_file_reduction, group, library_datasets, reduced_weights)


def voronoi_reduction(hdf_file, hdf_file_reduction, tolerance_momentum, tolerance_position):
    """ Create name of reducted file, array of momentum """

    name_hdf_file_reduction = ''

    if hdf_file != '':
        if os.path.exists(hdf_file):
            name = hdf_file[:-4]
            idx_of_name = name.rfind('/')
            if idx_of_name != -1:
                name_hdf_file_reduction = hdf_file_reduction + hdf_file[idx_of_name + 1: -6] + 'reduction.h5'
            else:
                name_hdf_file_reduction = hdf_file_reduction + hdf_file[:-3] + '.h5'

            tolerances = [tolerance_momentum, tolerance_position]
            voronoi_algorithm(hdf_file, hdf_file_reduction, tolerances)
        else:
            print('The .hdf file does not exist')


def get_particles_groups(hdf_file_name, hdf_file_reduction_name):
    copyfile(hdf_file_name, hdf_file_reduction_name)
    hdf_file = h5py.File(hdf_file_name, 'a')
    hdf_file_reduction = h5py.File(hdf_file_reduction_name, 'a')
    particles_name = read_hdf_file.get_particles_name(hdf_file_reduction)
    particles_collect = read_hdf_file.ParticlesGroups(particles_name)
    hdf_file.visititems(particles_collect)

    return particles_collect, hdf_file_reduction


def voronoi_algorithm(hdf_file_name, hdf_file_reduction_name, tolerances):
    """ Create copy of  original file, iterate base groups"""

    particles_collect, hdf_file_reduction = get_particles_groups(hdf_file_name, hdf_file_reduction_name)

    for group in particles_collect.particles_groups:
        data, weights, dimensions \
            = read_hdf_file.read_points_group(group)

        parameters = Voronoi_algorithm.VoronoiMergingAlgorithmParameters(tolerances, dimensions.dimension_position)
        algorithm = Voronoi_algorithm.VoronoiMergingAlgorithm(parameters)

        reduced_data, reduced_weights = algorithm.run(data, weights)

        library_datasets = read_hdf_file.create_datasets_from_vector(reduced_data, dimensions)
        read_hdf_file.write_group_values(hdf_file_reduction, group, library_datasets, reduced_weights)


def random_thinning_algorithm(hdf_file_name, hdf_file_reduction_name, reduction_percent):

    algorithm = Random_thinning_algorithm.RandomThinningAlgorithm(reduction_percent)
    thinning_base_procedure(hdf_file_name, hdf_file_reduction_name, algorithm)


def number_conservative_thinning_algorithm(hdf_file_name, hdf_file_reduction_name, amount_sample_procedure):
    algorithm = Number_conservative_thinning_algorithm.Number_conservative_thinning_algorithm(amount_sample_procedure)
    thinning_base_procedure(hdf_file_name, hdf_file_reduction_name, algorithm)


def leveling_thinning_algorithm(hdf_file_name, hdf_file_reduction_name, leveling_coefficient):
    algorithm = Leveling_thinning_algorithm.Leveling_thinning_algorithm(leveling_coefficient)
    thinning_base_procedure(hdf_file_name, hdf_file_reduction_name, algorithm)


def energy_conservative_thinning_algorithm(hdf_file_name, hdf_file_reduction_name, amount_sample_procedure):
    algorithm = Energy_conservative_thinning_algorithm.Energy_conservative_thinning_algorithm(amount_sample_procedure)
    thinning_base_procedure(hdf_file_name, hdf_file_reduction_name, algorithm)


def k_means_merge_avg_algorithm(hdf_file_name, hdf_file_reduction_name, reduction_percent):
    algorithm = k_means_clustering_algorithm.K_means_clustering_algorithm(reduction_percent)
    thinning_base_procedure(hdf_file_name, hdf_file_reduction_name, algorithm)


def thinning_base_procedure(hdf_file_name, hdf_file_reduction_name, algorithm):

    particles_collect, hdf_file_reduction = get_particles_groups(hdf_file_name, hdf_file_reduction_name)

    for group in particles_collect.particles_groups:
        data, weights, dimensions\
            = read_hdf_file.read_points_group(group)
        num_particles, num_particles_offset = read_hdf_file.read_patches_values(group)

        reduced_data, reduced_weights, result_num_particles =\
            iterate_patches(data, weights, num_particles_offset, algorithm)
        library_datasets = read_hdf_file.create_datasets_from_vector(reduced_data, dimensions)

        read_hdf_file.write_group_values(hdf_file_reduction, group, library_datasets, reduced_weights)


def k_means_algorithm(hdf_file_name, hdf_file_reduction_name, reduction_percent):
    """ Create copy of  original file, iterate base groups"""

    particles_collect, hdf_file_reduction = get_particles_groups(hdf_file_name, hdf_file_reduction_name)

    for group in particles_collect.particles_groups:
        data, weights, dimensions \
            = read_hdf_file.read_points_group(group)

        parameters = k_means_clustering_algorithm.K_means_clustering_algorithm_Parameters(reduction_percent)
        algorithm = k_means_clustering_algorithm.K_means_clustering_algorithm(parameters)

        reduced_data, reduced_weights = algorithm._run(data, weights)
        library_datasets = read_hdf_file.create_datasets_from_vector(reduced_data, dimensions)
        read_hdf_file.write_group_values(hdf_file_reduction, group, library_datasets, reduced_weights)


def Vranic_algorithm_algorithm(hdf_file_name, hdf_file_reduction_name, momentum_tolerance, type_particles):
    """ Create copy of  original file, iterate base groups"""

    particles_collect, hdf_file_reduction = get_particles_groups(hdf_file_name, hdf_file_reduction_name)

    for group in particles_collect.particles_groups:
        data, weights, dimensions \
            = read_hdf_file.read_points_group(group)
        mass = read_hdf_file.read_mass(group)

        parameters = Vranic_algorithm.Vranic_merging_algorithm_parameters(momentum_tolerance, dimensions, type_particles)
        algorithm = Vranic_algorithm.Vranic_merging_algorithm(parameters)
        reduced_data, reduced_weights = algorithm._run(data, weights, mass)
        library_datasets = read_hdf_file.create_datasets_from_vector(reduced_data, dimensions)
        read_hdf_file.write_group_values(hdf_file_reduction, group, library_datasets, reduced_weights)


def iterate_patches(data, weights, num_particles_offset, algorithm):

    ranges_patches = num_particles_offset

    ranges_patches.astype(int)


    reduced_data = []
    reduced_weights = []
    result_num_particles = []


    for i in range(0, len(ranges_patches) - 1):
        start = int(ranges_patches[i])
        end = int(ranges_patches[i + 1])
        copy_data = copy.deepcopy(data[start:end])

        copy_weights = copy.deepcopy(weights[start:end])
        reduced_data_patch, reduced_weight_patch = algorithm._run(copy_data, copy_weights)

        for point in reduced_data_patch:
            reduced_data.append(point)

        for weight in reduced_weight_patch:
            reduced_weights.append(weight)
        result_num_particles.append(len(data))

    return reduced_data, reduced_weights, result_num_particles


if __name__ == "__main__":
    """ Parse arguments from command line """

    parser = argparse.ArgumentParser(description="voronoi reduction")

    parser.add_argument("-algorithm", metavar='algorithm', type=str,
                        help="hdf file without patches")

    parser.add_argument("-hdf", metavar='hdf_file', type=str,
                        help="hdf file without patches")

    parser.add_argument("-hdf_re", metavar='hdf_file_reduction', type=str,
                        help="reducted hdf file")

    parser.add_argument("-reduction_percent", metavar='reduction_percent', type=float,
                        help="part of the particles to reduce")

    parser.add_argument("-sample_amount", metavar='sample_amount', type=int,
                        help="amount of sample ")

    parser.add_argument("-momentum_tol", metavar='tolerance_momentum', type=float,
                        help="tolerance of momentum")

    parser.add_argument("-momentum_pos", metavar='tolerance_position', type=float,
                        help="tolerance of position")

    parser.add_argument("-particles_type", metavar='particles_type', type=str,
                        help="types of particles")

    parser.add_argument("-leveling_coefficient", metavar='leveling_coefficient', type=float,
                        help="leveling_coefficient")

    args = parser.parse_args()

    if args.algorithm == 'voronoi':
        voronoi_reduction(args.hdf, args.hdf_re, args.momentum_tol, args.momentum_pos)
    elif args.algorithm == 'random':
        random_thinning_algorithm(args.hdf, args.hdf_re, args.reduction_percent)
    elif args.algorithm == 'number_conservative':
        number_conservative_thinning_algorithm(args.hdf, args.hdf_re, args.sample_amount)
    elif args.algorithm == 'energy_conservative':
        energy_conservative_thinning_algorithm(args.hdf, args.hdf_re, args.sample_amount)
    elif args.algorithm == 'kmeans':
        k_means_algorithm(args.hdf, args.hdf_re, args.reduction_percent)
    elif args.algorithm == 'kmeans_avg':
        k_means_merge_avg_algorithm(args.hdf, args.hdf_re, args.reduction_percent)
    elif args.algorithm == 'vranic_algorithm':
        Vranic_algorithm_algorithm(args.hdf, args.hdf_re, args.momentum_tol, args.particles_type)
    elif args.algorithm == 'leveling':
        leveling_thinning_algorithm(args.hdf, args.hdf_re, args.leveling_coefficient)


