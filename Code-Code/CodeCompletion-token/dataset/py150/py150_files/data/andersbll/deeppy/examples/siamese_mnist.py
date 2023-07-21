#!/usr/bin/env python

"""
Siamese networks
================

"""

import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import offsetbox
import deeppy as dp

# Fetch MNIST data
dataset = dp.dataset.MNIST()
x_train, y_train, x_test, y_test = dataset.arrays(flat=True, dp_dtypes=True)

# Normalize pixel intensities
scaler = dp.StandardScaler()
x_train = scaler.fit_transform(x_train)
x_test = scaler.transform(x_test)

# Generate image pairs
n_pairs = 100000
x1 = np.empty((n_pairs, 28*28), dtype=dp.float_)
x2 = np.empty_like(x1, dtype=dp.float_)
y = np.empty(n_pairs, dtype=dp.int_)
n_imgs = x_train.shape[0]
n = 0
while n < n_pairs:
    i = random.randint(0, n_imgs-1)
    j = random.randint(0, n_imgs-1)
    if i == j:
        continue
    x1[n, ...] = x_train[i]
    x2[n, ...] = x_train[j]
    if y_train[i] == y_train[j]:
        y[n] = 1
    else:
        y[n] = 0
    n += 1

# Prepare network feeds
batch_size = 128
train_feed = dp.SupervisedSiameseFeed(x1, x2, y, batch_size=batch_size)

# Setup network
w_gain = 1.5
w_decay = 1e-4
net = dp.SiameseNetwork(
    siamese_layers=[
        dp.Affine(
            n_out=1024,
            weights=dp.Parameter(dp.AutoFiller(w_gain), weight_decay=w_decay),
        ),
        dp.ReLU(),
        dp.Affine(
            n_out=1024,
            weights=dp.Parameter(dp.AutoFiller(w_gain), weight_decay=w_decay),
        ),
        dp.ReLU(),
        dp.Affine(
            n_out=2,
            weights=dp.Parameter(dp.AutoFiller(w_gain)),
        ),
    ],
    loss=dp.ContrastiveLoss(margin=1.0),
)

# Train network
learn_rate = 0.01/batch_size
learn_rule = dp.RMSProp(learn_rate)
trainer = dp.GradientDescent(net, train_feed, learn_rule)
trainer.train_epochs(n_epochs=15)


# Plot 2D embedding
test_feed = dp.Feed(x_test)
x_test = np.reshape(x_test, (-1,) + dataset.img_shape)
embedding = net.embed(test_feed)
embedding -= np.min(embedding, 0)
embedding /= np.max(embedding, 0)

plt.figure()
ax = plt.subplot(111)
shown_images = np.array([[1., 1.]])
for i in range(embedding.shape[0]):
    dist = np.sum((embedding[i] - shown_images)**2, 1)
    if np.min(dist) < 6e-4:
        # don't show points that are too close
        continue
    shown_images = np.r_[shown_images, [embedding[i]]]
    imagebox = offsetbox.AnnotationBbox(
        offsetbox.OffsetImage(x_test[i], zoom=0.6, cmap=plt.cm.gray_r),
        xy=embedding[i], frameon=False
    )
    ax.add_artist(imagebox)

plt.xticks([]), plt.yticks([])
plt.title('Embedding from the last layer of the network')
