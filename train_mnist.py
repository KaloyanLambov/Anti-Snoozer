# TensorFlow provides the deep learning framework and built-in MNIST dataset.
import tensorflow as tf

# Keras layers and model-building utilities.
from tensorflow.keras import layers, models

# Utility for generating augmented (randomly modified) training images.
from tensorflow.keras.preprocessing.image import ImageDataGenerator


# ---------------------------------------------------------------------------
# Load the MNIST handwritten digit dataset.
# x_train/x_test contain grayscale images of digits (0–9).
# y_train/y_test contain the corresponding labels.
# ---------------------------------------------------------------------------
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()


# ---------------------------------------------------------------------------
# Preprocess images:
# - Add a channel dimension so images become (28, 28, 1) instead of (28, 28).
# - Normalize pixel values from [0, 255] to [0.0, 1.0].
# This helps the neural network train more efficiently.
# ---------------------------------------------------------------------------
x_train = x_train[..., None] / 255.0
x_test  = x_test[..., None]  / 255.0


# ---------------------------------------------------------------------------
# Data augmentation:
# Randomly transform training images to create more variation.
#
# This helps the model generalize better to real-world handwritten digits,
# especially if inputs are messy, off-center, tilted, or slightly distorted.
#
# rotation_range      -> random rotation up to ±12 degrees
# width_shift_range   -> horizontal movement up to 12% of image width
# height_shift_range  -> vertical movement up to 12% of image height
# zoom_range          -> zoom in/out by up to 12%
# shear_range         -> slant/skew the digit slightly
# ---------------------------------------------------------------------------
datagen = ImageDataGenerator(
    rotation_range=12,
    width_shift_range=0.12,
    height_shift_range=0.12,
    zoom_range=0.12,
    shear_range=8,
)

# Compute any statistics needed by the augmentation pipeline.
# (Not strictly necessary for these augmentations, but harmless.)
datagen.fit(x_train)


# ---------------------------------------------------------------------------
# Build a Convolutional Neural Network (CNN).
#
# Architecture:
# Input (28x28x1)
#   ↓
# Conv2D(32 filters)
#   ↓
# Batch Normalization
#   ↓
# Max Pooling
#   ↓
# Conv2D(64 filters)
#   ↓
# Batch Normalization
#   ↓
# Max Pooling
#   ↓
# Conv2D(64 filters)
#   ↓
# Flatten
#   ↓
# Dense(256)
#   ↓
# Dropout(40%)
#   ↓
# Dense(10) → probabilities for digits 0–9
# ---------------------------------------------------------------------------
model = models.Sequential([
    # Input layer expects a 28×28 grayscale image.
    layers.Input(shape=(28, 28, 1)),

    # Detect simple features such as edges and strokes.
    layers.Conv2D(32, 3, activation="relu"),

    # Normalize activations to stabilize and speed up training.
    layers.BatchNormalization(),

    # Reduce spatial dimensions while keeping important features.
    layers.MaxPooling2D(),

    # Learn more complex patterns from earlier features.
    layers.Conv2D(64, 3, activation="relu"),
    layers.BatchNormalization(),
    layers.MaxPooling2D(),

    # Final convolutional feature extractor.
    layers.Conv2D(64, 3, activation="relu"),

    # Convert feature maps into a 1D vector.
    layers.Flatten(),

    # Fully connected layer for classification.
    layers.Dense(256, activation="relu"),

    # Randomly disable 40% of neurons during training to reduce overfitting.
    layers.Dropout(0.4),

    # Output layer:
    # 10 neurons (one per digit), softmax converts outputs to probabilities.
    layers.Dense(10, activation="softmax"),
])


# ---------------------------------------------------------------------------
# Configure training.
#
# optimizer="adam"
#     Adaptive optimization algorithm that generally works well by default.
#
# loss="sparse_categorical_crossentropy"
#     Appropriate because labels are integer class IDs (0–9).
#
# metrics=["accuracy"]
#     Report classification accuracy during training and evaluation.
# ---------------------------------------------------------------------------
model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)


# ---------------------------------------------------------------------------
# Train the model.
#
# datagen.flow(...) continuously produces augmented versions of the training
# images, effectively creating endless variations of the original dataset.
#
# batch_size=128
#     Number of samples processed before each weight update.
#
# epochs=15
#     Number of complete passes through the training data.
#
# validation_data=(x_test, y_test)
#     Evaluate performance on unseen test data after each epoch.
# ---------------------------------------------------------------------------
model.fit(
    datagen.flow(x_train, y_train, batch_size=128),
    epochs=15,
    validation_data=(x_test, y_test),
)


# ---------------------------------------------------------------------------
# Evaluate the trained model on the test dataset.
# Returns:
#   loss -> final loss value
#   acc  -> classification accuracy
# ---------------------------------------------------------------------------
loss, acc = model.evaluate(x_test, y_test)

# Print accuracy as a percentage (e.g., 99.2%).
print(f"Test accuracy: {acc:.1%}")


# ---------------------------------------------------------------------------
# Save the trained model to disk.
# The .keras format preserves architecture, weights, and training config.
# ---------------------------------------------------------------------------
model.save("mnist_model.keras")