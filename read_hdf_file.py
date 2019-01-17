import h5py
import re
import Voronoi_algorithm


class ParticlesFunctor():
    """

    Collect values(weighting, position, momentum) from paticle dataset in hdf file.
    positions -- group of position coords
    momentum -- group of momentum coords
    weightins -- values of weights for particles

    """

    def __init__(self):
        self.particles_groups = []
        self.positions = []
        self.momentum = []
        self.weighting = []


    def __call__(self, name, node):

        if isinstance(node, h5py.Dataset):
            if node.name.endswith('weighting'):
                self.weighting = node.value

        if isinstance(node, h5py.Group):
            if node.name.endswith('position'):
                self.positions.append(node)

            if node.name.endswith('momentum'):
                self.momentum.append(node)

        return None


class ParticlesGroups():
    """

    Collect particles groups from hdf file
    particles_name -- name of main partcles group

    """

    def __init__(self, particles_name):

        self.name_particles = particles_name
        self.particles_groups = []

    def __call__(self, name, node):
        if isinstance(node, h5py.Group):
            name_idx = node.name.find(self.name_particles)
            if name_idx != -1:
                group_particles_name = node.name[name_idx + len(self.name_particles) + 1:]
                if group_particles_name.find('/') == -1 and group_particles_name != '':
                    self.particles_groups.append(node)
        return None


class DatasetWriter():
    """

    Write dataset into result hdf file
    name_dataset -- name recorded dataset
    hdf_file -- result hdf file
    result_points -- points to write to hdf file

    """

    def __init__(self, hdf_file, result_points, name_dataset):

        self.vector_x = []
        self.vector_y = []
        self.vector_z = []
        self.weighting = []
        self.hdf_file = hdf_file
        self.name_dataset = name_dataset
        self.demention = len(result_points[0].points[self.name_dataset][0].coords)

        for point in result_points:

            if point.points[self.name_dataset] != None:

                vector_coords = point.points[self.name_dataset][0].coords
                if self.demention == 2:
                    self.vector_x.append(vector_coords[0])
                    self.vector_y.append(vector_coords[1])
                if self.demention == 3:
                    self.vector_x.append(vector_coords[0])
                    self.vector_y.append(vector_coords[1])
                    self.vector_y.append(vector_coords[2])

    def __call__(self, name, node):

        if isinstance(node, h5py.Dataset):

            dataset_x = self.name_dataset + '/x'
            dataset_y = self.name_dataset + '/y'
            dataset_z = self.name_dataset + '/z'

            if node.name.endswith(dataset_x):
                node_name = node.name
                del self.hdf_file[node.name]
                dset = self.hdf_file.create_dataset(node_name, data=self.vector_x)
            elif node.name.endswith(dataset_y):
                node_name = node.name
                del self.hdf_file[node.name]
                dset = self.hdf_file.create_dataset(node_name, data=self.vector_y)

            elif node.name.endswith(dataset_z):
                node_name = node.name
                del self.hdf_file[node.name]
                dset = self.hdf_file.create_dataset(node_name, data=self.vector_z)

            elif node.name.endswith('weighting'):
                node_name = node.name
                del self.hdf_file[node.name]
                dset = self.hdf_file.create_dataset(node_name, data=self.weighting)

        return None


class DatasetReader():
    """

     Read datasets values from hdf file
     name_dataset -- name of base group

    """

    def __init__(self, name_dataset):
        self.vector_x = []
        self.vector_y = []
        self.vector_z = []
        self.name_dataset = name_dataset

    def __call__(self, name, node):

        dataset_x = self.name_dataset + '/x'
        dataset_y = self.name_dataset + '/y'
        dataset_z = self.name_dataset + '/z'
        if isinstance(node, h5py.Dataset):
            if node.name.endswith(dataset_x):
                self.vector_x = node.value

            if node.name.endswith(dataset_y):
                self.vector_y = node.value

            if node.name.endswith(dataset_z):
                self.vector_z = node.value

        return None

    def get_demention(self):
        """

         get dimension of particles datasets

        """

        size = 0
        if len(self.vector_x) > 0:
            if len(self.vector_y) > 0:
                if len(self.vector_z) > 0:
                    size = 3
                else:
                    size = 2
            else:
                size = 1

        return size


def get_particles_name(hdf_file):
    """ Get name of particles group """

    particles_name = ''
    if hdf_file.attrs.get('particlesPath') != None:
        particles_name = hdf_file.attrs.get('particlesPath')
        particles_name = decode_name(particles_name)
    else:
        particles_name = 'particles'
    return particles_name


def decode_name(attribute_name):
    """ Decode name from binary """

    decoding_name = attribute_name.decode('ascii', errors='ignore')
    decoding_name = re.sub(r'\W+', '', decoding_name)
    return decoding_name


def create_point_array(coord_collection, weighting):
    """

    create array of 2-d, 3-d points from datasets
    coord_collection -- datasets from hdf file

    """

    point_array = []

    demention = coord_collection.get_demention()

    if demention == 3:
        for i in range(0, len(coord_collection.vector_x)):
            point_array.append(Voronoi_algorithm.Point([coord_collection.vector_x[i], coord_collection.vector_y[i],
                                      coord_collection.vector_z[i]], weighting[i]))

    elif demention == 2:
        for i in range(0, len(coord_collection.vector_x)):
            point_array.append(Voronoi_algorithm.Point([coord_collection.vector_x[i], coord_collection.vector_y[i]], weighting[i]))

    return point_array


def create_points_library(coord_collect, momuntum_collect, weighting):
    """

    create set of postion points and momentum points

    """
    pointMomentum = create_point_array(momuntum_collect, weighting)

    points = {}
    points['position'] = pointArraysCoord
    points['momentum'] = pointMomentum

    return points


def read_group_values(group):
    """

    convert values from position and momentum datasets into points
    group -- base group of points from hdf file

    """

    group.visititems(hdf_datasets)
    weighting = hdf_datasets.weighting
    position_values = Dataset_reader('position')
    momentum_values = Dataset_reader('momentum')
    position_group = hdf_datasets.positions[0]
    momentum_group = hdf_datasets.momentum[0]
    position_group.visititems(position_values)
    momentum_group.visititems(momentum_values)
    points = create_points_library(position_values, momentum_values, weighting)
    return points


def write_group_values(hdf_file_reduction, group, result):
    """

    write values from point library to hdf file
    hdf_file_reduction -- result file
    group -- base group of partilces from original file
    result -- library points

    """

    hdf_datasets = ParticlesFunctor()
    group.visititems(hdf_datasets)
    position_values = DatasetReader('position')
    momentum_values = DatasetReader('momentum')
    position_group = hdf_datasets.positions[0]
    momentum_group = hdf_datasets.momentum[0]
    position_group.visititems(position_values)
    momentum_group.visititems(momentum_values)
    writen_position = DatasetWriter(hdf_file_reduction, result, 'position')
    writen_momentum = DatasetWriter(hdf_file_reduction, result, 'momentum')
    position_group.visititems(writen_position)
    momentum_group.visititems(writen_momentum)
    