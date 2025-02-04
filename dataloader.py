import os
import torch
import torchvision.transforms as transforms
import torchvision.datasets as datasets
import medmnist
from medmnist.dataset import *

class WrapOCTMNIST(OCTMNIST):
    def __init__(self, **kwargs):
        super(WrapOCTMNIST, self).__init__(**kwargs)

    def __getitem__(self, idx):
        image, label = super(WrapOCTMNIST, self).__getitem__(idx)
        return image, int(label[0])

class WrapTissueMNIST(TissueMNIST):
    def __init__(self, **kwargs):
        super(WrapTissueMNIST, self).__init__(**kwargs)

    def __getitem__(self, idx):
        image, label = super(WrapTissueMNIST, self).__getitem__(idx)
        return image, int(label[0])

def get_dataloaders(args):
    train_loader, val_loader, test_loader = None, None, None
    if args.data == 'cifar10':
        # normalize = transforms.Normalize(mean=[0.4914, 0.4824, 0.4467],
        #                                  std=[0.2471, 0.2435, 0.2616])
        train_set = datasets.CIFAR10(args.data_root, train=True, download=True,
                                     transform=transforms.Compose([
                                        # transforms.RandomCrop(32, padding=4),
                                        # transforms.RandomHorizontalFlip(),
                                        transforms.Resize((224, 224)),
                                        transforms.ToTensor(),
                                        # normalize
                                     ]))
        test_set = datasets.CIFAR10(args.data_root, train=False, download=True,
                                   transform=transforms.Compose([
                                    transforms.Resize((224, 224)),
                                    transforms.ToTensor(),
                                #     normalize
                                   ]))
        val_set = None
    elif args.data == 'cifar100':
        # normalize = transforms.Normalize(mean=[0.5071, 0.4867, 0.4408],
        #                                  std=[0.2675, 0.2565, 0.2761])
        train_set = datasets.CIFAR100(args.data_root, train=True, download=True,
                                      transform=transforms.Compose([
                                        # transforms.RandomCrop(32, padding=4),
                                        # transforms.RandomHorizontalFlip(),
                                        transforms.Resize((224, 224)),
                                        transforms.ToTensor(),
                                        # normalize
                                      ]))
        test_set = datasets.CIFAR100(args.data_root, train=False, download=True,
                                    transform=transforms.Compose([
                                        transforms.Resize((224, 224)),
                                        transforms.ToTensor(),
                                        # normalize
                                    ]))
        val_set = None
    elif args.data.endswith('mnist'):
        if args.data == 'octmnist':
            dataclass = WrapOCTMNIST
        elif args.data == 'tissuemnist':
            dataclass = WrapTissueMNIST
        else:
            raise NotImplementedError

        train_set = dataclass(root=args.data_root, split='train', download=True, transform=transforms.Compose([transforms.Resize((96, 96)), transforms.ToTensor()]))
        val_set = dataclass(root=args.data_root, split='val', download=True, transform=transforms.Compose([transforms.Resize((96, 96)), transforms.ToTensor()]))
        test_set = dataclass(root=args.data_root, split='test', download=True, transform=transforms.Compose([transforms.Resize((96, 96)), transforms.ToTensor()]))

    else:
        # ImageNet
        traindir = os.path.join(args.data_root, 'train')
        valdir = os.path.join(args.data_root, 'val')
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
        train_set = datasets.ImageFolder(traindir, transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize
        ]))
        val_set = datasets.ImageFolder(valdir, transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            normalize
        ]))
    if args.use_valid:
        if val_set is None:
            train_set_index = torch.randperm(len(train_set))
            if os.path.exists(os.path.join(args.save, 'index.pth')):
                print('!!!!!! Load train_set_index !!!!!!')
                train_set_index = torch.load(os.path.join(args.save, 'index.pth'))
            else:
                print('!!!!!! Save train_set_index !!!!!!')
                torch.save(train_set_index, os.path.join(args.save, 'index.pth'))
            if args.data.startswith('cifar'):
                num_sample_valid = 5000
            else:
                num_sample_valid = 50000

            if 'train' in args.splits:
                train_loader = torch.utils.data.DataLoader(
                    train_set, batch_size=args.batch_size,
                    sampler=torch.utils.data.sampler.SubsetRandomSampler(
                        train_set_index[:-num_sample_valid]),
                    num_workers=args.workers, pin_memory=False)
            if 'val' in args.splits:
                val_loader = torch.utils.data.DataLoader(
                    train_set, batch_size=args.batch_size,
                    sampler=torch.utils.data.sampler.SubsetRandomSampler(
                        train_set_index[-num_sample_valid:]),
                    num_workers=args.workers, pin_memory=False)
            if 'test' in args.splits:
                test_loader = torch.utils.data.DataLoader(
                    test_set,
                    batch_size=args.batch_size, shuffle=False,
                    num_workers=args.workers, pin_memory=False)
        else:
            if 'train' in args.splits:
                train_loader = torch.utils.data.DataLoader(
                    train_set, batch_size=args.batch_size,
                    num_workers=args.workers, pin_memory=False)
            if 'val' in args.splits:
                val_loader = torch.utils.data.DataLoader(
                    val_set, batch_size=args.batch_size,
                    num_workers=args.workers, pin_memory=False)
            if 'test' in args.splits:
                test_loader = torch.utils.data.DataLoader(
                    test_set,
                    batch_size=args.batch_size, shuffle=False,
                    num_workers=args.workers, pin_memory=False)
    else:
        if 'train' in args.splits:
            train_loader = torch.utils.data.DataLoader(
                train_set,
                batch_size=args.batch_size, shuffle=True,
                num_workers=args.workers, pin_memory=False)
        if 'val' or 'test' in args.splits:
            val_loader = torch.utils.data.DataLoader(
                test_set,
                batch_size=args.batch_size, shuffle=False,
                num_workers=args.workers, pin_memory=False)
            test_loader = val_loader

    return train_loader, val_loader, test_loader
