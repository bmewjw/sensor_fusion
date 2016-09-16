import math
import random

import numpy as np
from matplotlib import pyplot as plt

import seaborn as sns


def generate(intersect, slope, sensor_sigma, occupant_range, occupant_sigma, datapoints=1000):
    """Generates fake sensor data"""

    fake_data = {
        'occupants': [],
        'reading': []}

    for _ in range(datapoints):
        real_occupants = random.randrange(occupant_range + 1)
        noisy_occupants = max(0, random.gauss(real_occupants, occupant_sigma))
        reading = intersect + noisy_occupants * slope
        reading = random.gauss(reading, sensor_sigma)
        fake_data['occupants'].append(real_occupants)
        fake_data['reading'].append(reading)

    return fake_data


def plot(data, filename):
    plt.cla()
    plt.scatter(x, y)
    slope, intercept = np.polyfit(data["occupants"], data["reading"], 1)
    occupant_range = np.array(
        range(min(data["occupants"]), max(data["occupants"]))
    )
    fit = occupant_range * slope + intercept
    plt.plot(occupant_range, fit)


def fit(data):

    slope, intercept = np.polyfit(data["occupants"], data["reading"], 1)
    error = 0.0
    n_samples = len(data["occupants"])
    for occupants, reading in zip(data["occupants"], data["reading"]):
        error += (occupants * slope + intercept - reading)**2

    sigma = np.sqrt(error / (n_samples - 1))

    def sensor_model(occupants):
        return occupants * slope + intercept, sigma

    def predictor(sensor_reading):
        return (sensor_reading - intercept) / slope, sigma / slope

    return sensor_model, predictor


def round_up(number, scale):
    return int(math.ceil(number / float(scale)) * scale)


def round_down(number, scale):
    return int(math.floor(number / float(scale)) * scale)


def plot_sensor_model(data, sensor_model, filename, round_level=10):
    occupant_vector = np.array(
        range(min(data["occupants"]) - 1, max(data["occupants"]) + 2)
    )
    fit_vector = np.array([sensor_model(o)[0] for o in occupant_vector])
    _, sigma = sensor_model(occupant_vector[0])
    error_vector = [sigma] * len(occupant_vector)

    plt.clf()
    ax = plt.gca()
    ax.set_xlim([occupant_vector[0], occupant_vector[-1]])
    ax.set_ylim([round_down(min(data["reading"]), round_level),
                 round_up(max(data["reading"]), round_level)])

    ax = sns.regplot(
        x=np.array(data["occupants"]),
        y=np.array(data["reading"]),
        marker='x',
        fit_reg=False
    )
    ax.plot(occupant_vector, fit_vector)

    x_range = np.linspace(ax.get_xlim()[0], ax.get_xlim()[1], 100)
    y_range = np.linspace(ax.get_ylim()[0], ax.get_ylim()[1], 100)

    xx, yy = np.meshgrid(x_range, y_range)
    zz = xx + yy

    for i in range(len(x_range)):
        for j in range(len(y_range)):
            zz[j, i] = gaussian(yy[j, i], *sensor_model(xx[j, i]))

    pal = sns.light_palette("green", as_cmap=True)


    im = plt.imshow(zz,  interpolation='bilinear', origin='lower',
                    cmap=pal, alpha=0.5, aspect='auto',
                    extent=(x_range[0], x_range[-1], y_range[0], y_range[-1]))
    cb = plt.colorbar(im, orientation='vertical', ticks=[
        gaussian(3 * sigma, 0, sigma),
        gaussian(2 * sigma, 0, sigma),
        gaussian(sigma, 0, sigma),
        gaussian(0, 0, sigma),
    ],
        drawedges=True
    )
    cb.set_ticklabels(['$3 \sigma$', '$2 \sigma$',
                       '$\sigma$', 'max'], update_ticks=True)
    plt.savefig(filename)


def plot_predictor(reading_range, predictor, filename, round_level=1, readings=[]):

    palette = sns.color_palette()

    reading_vector = np.linspace(*reading_range)
    fit_vector = np.array([predictor(r)[0] for r in reading_vector])
    _, sigma = predictor(reading_vector[0])
    # error_vector = [sigma] * len(reading_vector)

    plt.clf()
    ax = plt.gca()
    ax.set_xlim([reading_vector[0], reading_vector[-1]])
    ax.set_ylim([round_down(fit_vector[0], round_level),
                 round_up(fit_vector[-1], round_level)])

    ax.plot(reading_vector, fit_vector, color=palette[1])

    x_range = np.linspace(ax.get_xlim()[0], ax.get_xlim()[1], 100)
    y_range = np.linspace(ax.get_ylim()[0], ax.get_ylim()[1], 100)

    xx, yy = np.meshgrid(x_range, y_range)
    zz = xx + yy

    for i in range(len(x_range)):
        for j in range(len(y_range)):
            zz[j, i] = gaussian(yy[j, i], *predictor(xx[j, i]))

    if readings:
        ax.vlines(readings, ax.get_ylim()[0], ax.get_ylim()[-1], linestyles='dotted')

    pal = sns.light_palette("green", as_cmap=True)

    im = plt.imshow(zz,  interpolation='bilinear', origin='lower',
                    cmap=pal, alpha=0.5, aspect='auto',
                    extent=(x_range[0], x_range[-1], y_range[0], y_range[-1]))
    cb = plt.colorbar(im, orientation='vertical', ticks=[
        gaussian(3 * sigma, 0, sigma),
        gaussian(2 * sigma, 0, sigma),
        gaussian(sigma, 0, sigma),
        gaussian(0, 0, sigma),
    ],
        drawedges=True
    )
    cb.set_ticklabels(['$3 \sigma$', '$2 \sigma$',
                       '$\sigma$', 'max'], update_ticks=True)
    plt.savefig(filename)

def plot_readings(reading_vector, predictor, filename, x_range=[0,15], fuse=False):
    plt.clf()
    ax = plt.gca()
    x_vector = np.linspace(*x_range)
    palette = sns.color_palette()
    fusion = None
    for reading in reading_vector:
        occupants, sigma = predictor(reading)
        if fuse:
            if not fusion:
                fusion = occupants, sigma
            else:
                fusion = bayesian_update(fusion, (occupants, sigma))
        y_vector = 100*gaussian(x_vector, occupants, sigma)
        ax.plot(x_vector, y_vector, color=palette[1])
        ax.vlines(occupants, 0, max(y_vector), linestyles='dotted', label='{}ppm'.format(reading))



    if fuse:
        y_vector = 100*gaussian(x_vector, *fusion)
        ax.plot(x_vector, y_vector, color=palette[3])

    ax.set_ylim(0, 20)
    ax.set_xlim(*x_range)
    plt.savefig(filename)

def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.))) / (sig * np.sqrt(2. * np.pi))


def bayesian_update(gaussian_a, gaussian_b):
    mu_a, sigma_a = gaussian_a
    mu_b, sigma_b = gaussian_b
    mu = ((sigma_a**2)*mu_b + (sigma_b**2)*mu_a)/(sigma_a**2 + sigma_b**2)
    sigma = np.sqrt(((sigma_a*sigma_b)**2)/(sigma_a**2 + sigma_b**2))

    return mu, sigma

if __name__ == "__main__":

    co2_data = generate(350, 60, 10, 15, 5, 250)
    co2_sensor_model, co2_predictor = fit(co2_data)
    plot_sensor_model(co2_data, co2_sensor_model,
                      'co2_experiment.png', round_level=500)
    plot_predictor([0, 1500], co2_predictor, 'co2_predictor.png', round_level=10)
    plot_predictor([0, 1500], co2_predictor, 'co2_predictor1.png', round_level=10, readings=[733])
    plot_predictor([0, 1500], co2_predictor, 'co2_predictor2.png', round_level=10, readings=[733, 1037])
    plot_predictor([0, 1500], co2_predictor, 'co2_predictor3.png', round_level=10, readings=[733, 790, 1037, 500, 699])

    plot_readings([733], co2_predictor, 'co2_readings1.png', x_range=[0, 15])
    plot_readings([733, 1037], co2_predictor, 'co2_readings2a.png', x_range=[0, 15], fuse=False)
    plot_readings([733, 1037], co2_predictor, 'co2_readings2b.png', x_range=[0, 15], fuse=True)
    plot_readings([733, 790, 1037, 500, 699], co2_predictor, 'co2_readings3.png', x_range=[0, 15], fuse=True)

    # temp_data = generate(19, 0.6, 0.5, 15, 5, 250)
    # temp_sensor_model = fit(temp_data)
    # plot(temp_data, temp_sensor_model, 'temp_experiment.png', round_level=5)
