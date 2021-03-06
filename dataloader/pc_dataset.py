# -*- coding:utf-8 -*-
# author: Xinge
# @file: pc_dataset.py 

import os
import numpy as np
from torch.utils import data
import yaml
import pickle
import h5py
REGISTERED_PC_DATASET_CLASSES = {}


def register_dataset(cls, name=None):
    global REGISTERED_PC_DATASET_CLASSES
    if name is None:
        name = cls.__name__
    assert name not in REGISTERED_PC_DATASET_CLASSES, f"exist class: {REGISTERED_PC_DATASET_CLASSES}"
    REGISTERED_PC_DATASET_CLASSES[name] = cls
    return cls


def get_pc_model_class(name):
    global REGISTERED_PC_DATASET_CLASSES
    assert name in REGISTERED_PC_DATASET_CLASSES, f"available class: {REGISTERED_PC_DATASET_CLASSES}"
    return REGISTERED_PC_DATASET_CLASSES[name]


@register_dataset
class SemKITTI_sk(data.Dataset):
    def __init__(self, data_path, imageset='train',
                 return_ref=False, label_mapping="semantic-kitti.yaml", nusc=None):
        self.return_ref = return_ref
        with open(label_mapping, 'r') as stream:
            semkittiyaml = yaml.safe_load(stream)
        self.learning_map = semkittiyaml['learning_map']
        self.imageset = imageset
        if imageset == 'train':
            split = semkittiyaml['split']['train']
        elif imageset == 'val':
            split = semkittiyaml['split']['valid']
        elif imageset == 'test':
            split = semkittiyaml['split']['test']
        else:
            raise Exception('Split must be train/val/test')

        self.im_idx = []
        for i_folder in split:
            self.im_idx += absoluteFilePaths('/'.join([data_path, str(i_folder).zfill(2), 'velodyne']))

    def __len__(self):
        'Denotes the total number of samples'
        return len(self.im_idx)

    def __getitem__(self, index):
        raw_data = np.fromfile(self.im_idx[index], dtype=np.float32).reshape((-1, 4))
        if self.imageset == 'test':
            annotated_data = np.expand_dims(np.zeros_like(raw_data[:, 0], dtype=int), axis=1)
        else:
            annotated_data = np.fromfile(self.im_idx[index].replace('velodyne', 'labels')[:-3] + 'label',
                                         dtype=np.int32).reshape((-1, 1))
            annotated_data = annotated_data & 0xFFFF  # delete high 16 digits binary
            annotated_data = np.vectorize(self.learning_map.__getitem__)(annotated_data)

        data_tuple = (raw_data[:, :3], annotated_data.astype(np.uint8))
        if self.return_ref:
            data_tuple += (raw_data[:, 3],)
        return data_tuple

@register_dataset
class Dense(data.Dataset):
    def __init__(self, data_path, imageset='train',
                 return_ref=True, label_mapping="dense.yaml", nusc=None):
        self.return_ref = return_ref
        with open(label_mapping, 'r') as stream:
            semkittiyaml = yaml.safe_load(stream)
        self.learning_map = semkittiyaml['learning_map']
        self.imageset = imageset
        if imageset == 'train':
            split = semkittiyaml['split']['train']
        elif imageset == 'val':
            split = semkittiyaml['split']['valid']
        elif imageset == 'test':
            split = semkittiyaml['split']['test']
        else:
            raise Exception('Split must be train/val/test')

        self.im_idx = []
        for i_folder in split:
            self.im_idx += absoluteFilePaths('/'.join([data_path, i_folder]))
    def __len__(self):
        'Denotes the total number of samples'
        return len(self.im_idx)

    def __getitem__(self, index):
        with h5py.File(self.im_idx[index], "r") as f:
            raw_data = np.dstack(
                (np.array(
                    f["sensorX_1"]), np.array(
                    f["sensorY_1"]), np.array(
                    f["sensorZ_1"]), np.array(
                    f['distance_m_1']), np.array(
                    f['intensity_1']), np.array(
                    f['labels_1']
                )))
            raw_data = raw_data.astype(np.float32).transpose(2,0,1).reshape(6,-1)
            if self.imageset == 'test':
                annotated_data = np.expand_dims(np.zeros_like(raw_data[:, 0], dtype=int), axis=1)
            else:
                annotated_data = raw_data[5,:].astype(np.int32).reshape(-1,1)
                annotated_data = annotated_data & 0xFFFF  # delete high 16 digits binary
                annotated_data = np.vectorize(self.learning_map.__getitem__)(annotated_data)
            data_tuple = (raw_data[:3,:].transpose(1,0), annotated_data.astype(np.uint8))
            if self.return_ref:
                data_tuple += (raw_data[3, :].reshape(-1,1),)
            return data_tuple

@register_dataset
class CycleDense(data.Dataset):
    def __init__(self, data_path, imageset='train', clss = "clear",
                 return_ref=True, label_mapping="cycledense.yaml", nusc=None):
        self.return_ref = return_ref
        with open(label_mapping, 'r') as stream:
            semkittiyaml = yaml.safe_load(stream)
        self.learning_map = semkittiyaml['learning_map']
        self.imageset = imageset
        if imageset+clss == 'trainclear':
            split = semkittiyaml['split']['trainclear']
        elif imageset+clss == 'trainrain':
            split = semkittiyaml['split']['trainrain']
        elif imageset+clss == 'trainfog':
            split = semkittiyaml['split']['trainfog']
        elif imageset+clss == 'valclear':
            split = semkittiyaml['split']['valclear']
        elif imageset+clss == 'valrain':
            split = semkittiyaml['split']['valrain']
        elif imageset+clss == 'valfog':
            split = semkittiyaml['split']['valfog']
        elif imageset+clss == 'testclear':
            split = semkittiyaml['split']['testclear']
        elif imageset+clss == 'testrain':
            split = semkittiyaml['split']['testrain']
        elif imageset+clss == 'testfog':
            split = semkittiyaml['split']['testfog']
        else:
            raise Exception('Split must be train/val/test with class clear/rain/fog')

        self.im_idx = []
        for i_folder in split:
            self.im_idx += absoluteFilePaths('/'.join([data_path, i_folder]))
    def __len__(self):
        'Denotes the total number of samples'
        return len(self.im_idx)

    def __getitem__(self, index):
        with h5py.File(self.im_idx[index], "r") as f:
            raw_data = np.dstack(
                (np.array(
                    f["sensorX_1"]), np.array(
                    f["sensorY_1"]), np.array(
                    f["sensorZ_1"]), np.array(
                    f['distance_m_1']), np.array(
                    f['intensity_1']), np.array(
                    f['labels_1']
                )))
            raw_data = raw_data.astype(np.float32).transpose(2,0,1).reshape(6,-1)
            # if self.imageset == 'test':
            #     annotated_data = np.expand_dims(np.zeros_like(raw_data[:, 0], dtype=int), axis=1)
            # else:
            #     annotated_data = raw_data[5,:].astype(np.int32).reshape(-1,1)
            #     annotated_data = annotated_data & 0xFFFF  # delete high 16 digits binary
            #     annotated_data = np.vectorize(self.learning_map.__getitem__)(annotated_data)
            # data_tuple = (raw_data[:3,:].transpose(1,0), annotated_data.astype(np.uint8))
            data_tuple = (raw_data[:3,:].transpose(1,0),)

            if self.return_ref:
                data_tuple += (raw_data[3, :].reshape(-1,1),)
                print(len(data_tuple))
            return data_tuple

@register_dataset
class SemKITTI_nusc(data.Dataset):
    def __init__(self, data_path, imageset='train',
                 return_ref=False, label_mapping="nuscenes.yaml", nusc=None):
        self.return_ref = return_ref

        with open(imageset, 'rb') as f:
            data = pickle.load(f)

        with open(label_mapping, 'r') as stream:
            nuscenesyaml = yaml.safe_load(stream)
        self.learning_map = nuscenesyaml['learning_map']

        self.nusc_infos = data['infos']
        self.data_path = data_path
        self.nusc = nusc

    def __len__(self):
        'Denotes the total number of samples'
        return len(self.nusc_infos)

    def __getitem__(self, index):
        info = self.nusc_infos[index]
        lidar_path = info['lidar_path'][16:]
        lidar_sd_token = self.nusc.get('sample', info['token'])['data']['LIDAR_TOP']
        lidarseg_labels_filename = os.path.join(self.nusc.dataroot,
                                                self.nusc.get('lidarseg', lidar_sd_token)['filename'])

        points_label = np.fromfile(lidarseg_labels_filename, dtype=np.uint8).reshape([-1, 1])
        points_label = np.vectorize(self.learning_map.__getitem__)(points_label)
        points = np.fromfile(os.path.join(self.data_path, lidar_path), dtype=np.float32, count=-1).reshape([-1, 5])

        data_tuple = (points[:, :3], points_label.astype(np.uint8))
        if self.return_ref:
            data_tuple += (points[:, 3],)
        return data_tuple


def absoluteFilePaths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def SemKITTI2train(label):
    if isinstance(label, list):
        return [SemKITTI2train_single(a) for a in label]
    else:
        return SemKITTI2train_single(label)


def SemKITTI2train_single(label):
    remove_ind = label == 0
    label -= 1
    label[remove_ind] = 255
    return label


# load Semantic KITTI class info

def get_SemKITTI_label_name(label_mapping):
    with open(label_mapping, 'r') as stream:
        semkittiyaml = yaml.safe_load(stream)
    SemKITTI_label_name = dict()
    for i in sorted(list(semkittiyaml['learning_map'].keys()))[::-1]:
        SemKITTI_label_name[semkittiyaml['learning_map'][i]] = semkittiyaml['labels'][i]

    return SemKITTI_label_name


def get_nuScenes_label_name(label_mapping):
    with open(label_mapping, 'r') as stream:
        nuScenesyaml = yaml.safe_load(stream)
    nuScenes_label_name = dict()
    for i in sorted(list(nuScenesyaml['learning_map'].keys()))[::-1]:
        val_ = nuScenesyaml['learning_map'][i]
        nuScenes_label_name[val_] = nuScenesyaml['labels_16'][val_]

    return nuScenes_label_name

if __name__ == "__main__":
    from collections import Counter
   # data = SemKITTI_sk(r"/home/jinwei/SemanticKitti/dataset/sequences",label_mapping="/mrtstorage/users/jinwei/Cylinder3D/config/label_mapping/semantic-kitti.yaml")
   # print(data.__len__())
   # xyz, label = data[0]
   # print(xyz.shape, label.shape)
   # print(Counter(label.flatten().tolist()))
    data = CycleDense(r"/home/jinwei/dense",label_mapping=r"/home/jinwei/Cylinder3D/config/label_mapping/cycledense.yaml")
    print(data.__len__())
    xyz,ref = data[0]
    print(xyz.shape,ref.shape)
