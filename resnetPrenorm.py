import tensorflow as tf
from keras.datasets import cifar10
from tensorflow.keras.utils import to_categorical

import numpy as np

import sys

from TensorflowResNetPrenorm import ResNet
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import math

def normalize(train_data, test_data):
    mean = np.mean(train_data, axis=(0,1,2,3))
    std = np.mean(train_data, axis=(0,1,2,3))
    
    X_train = (train_data - mean) / std
    X_test = (test_data - mean) / std
    
    return X_train, X_test

def load_cifar10():
    (train_data, train_labels), (test_data, test_labels) = cifar10.load_data()
    #train_data, test_data =normalize(train_data, test_data)
    train_data = train_data.astype('float32') / 255
    test_data = test_data.astype('float32') / 255
    train_data_mean = np.mean(train_data, axis=0)
    train_data -= train_data_mean
    test_data -= train_data_mean

    train_labels = to_categorical(train_labels, 10)
    test_labels = to_categorical(test_labels, 10)
    
    seed = 1234
    np.random.seed(seed)
    np.random.shuffle(train_data)
    np.random.seed(seed)
    np.random.shuffle(train_labels)
    
    return train_data, train_labels, test_data, test_labels

def get_lr_metric(optimizer):
    def lr(y_true, y_pred):
        return optimizer.lr
    return lr

def Scheduler(epoch, lr):
    if epoch < 80:
        lr = .001
    elif epoch < 120:
        lr = .0001
    elif epoch < 160:
        lr = .00005
    elif epoch < 180:
        lr = .00001
    #print("\n\t Learning rate in epoch {} is {}\n".format(epoch, lr))
    return lr


def sch(epoch, lr):
    if epoch < 80:
        lr = .1
    elif epoch < 120:
        lr = .01
    elif epoch < 160:
        lr = .001
    elif epoch < 180:
        lr = .0001
    return lr

def largeSch(epoch, lr):
    if epoch < 2:
        lr = .01
    elif epoch < 80:
        lr = .1
    elif epoch < 120:
        lr = .01
    elif epoch < 160:
        lr = .001
    elif epoch < 180:
        lr = .0001
    return lr

def TestError(y_true, y_pred):
    temp = tf.keras.metrics.categorical_accuracy(y_true, y_pred)
    return (1 - temp) * 100

if (__name__ == "__main__"):
    train_data, train_labels, test_data, test_labels = load_cifar10()

    num = 3
    log_dir = "logs/"
    if (len(sys.argv) == 2):
        num = int(sys.argv[1])
    elif (len(sys.argv) == 3):
        num = int(sys.argv[1])
        dirname = sys.argv[2]
        log_dir = "logs/" + dirname + '/'

    resnet = ResNet(n=num)

    resnet.summary()
    tf.keras.utils.plot_model(resnet, resnet.name+"_identity.png", True)

    optimizer = tf.keras.optimizers.SGD(learning_rate=0.1, momentum=0.9)
    lr_metric = get_lr_metric(optimizer)
    lr_callback = tf.keras.callbacks.LearningRateScheduler(sch)
    if 6 * num + 1 > 100:
        lr_callback = tf.keras.callbacks.LearningRateScheduler(largeSch)
    
    resnet.compile(optimizer,
                   tf.keras.losses.CategoricalCrossentropy(),
                   metrics=['acc', TestError])


    log_dir += resnet.name
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)
    
    
    datagen = ImageDataGenerator(
        # set input mean to 0 over the dataset
        featurewise_center=False,
        # set each sample mean to 0
        samplewise_center=False,
        # divide inputs by std of dataset
        featurewise_std_normalization=False,
        # divide each input by its std
        samplewise_std_normalization=False,
        # apply ZCA whitening
        zca_whitening=False,
        # randomly rotate images in the range (deg 0 to 180)
        rotation_range=0,
        # randomly shift images horizontally
        width_shift_range=0.1,
        # randomly shift images vertically
        height_shift_range=0.1,
        # randomly flip images
        horizontal_flip=True,
        # randomly flip images
        vertical_flip=False)

    # compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied).
    datagen.fit(train_data)

    steps_per_epoch =  math.ceil(len(train_data) / 128)
    # fit the model on the batches generated by datagen.flow().

    resnet.fit(x=datagen.flow(train_data, train_labels, batch_size=128),
               batch_size=128, epochs=200, verbose=1,
               validation_data=(test_data, test_labels),
               steps_per_epoch=steps_per_epoch,
               callbacks=[lr_callback, tensorboard_callback])

    score = resnet.evaluate(test_data, test_labels)