# A live plotting script that reads from the latest log,
# and plots the data in real time.
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
import matplotlib.animation as animation
from matplotlib import style


def find_latest_log():
    log_dir = "../logs/"
    logs = os.listdir(log_dir)
    logs.sort()
    return log_dir + logs[-1]

# style.use('fivethirtyeight')

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

def animatedtraj(i):
    traj = pd.read_csv(log_file)
    df = pd.DataFrame(traj, columns=['x', 'y', 'z', 'target_req'])
    x = -df.x.to_numpy()
    img_req = df.target_req.to_numpy()
    y = df.y.to_numpy()
    x = -df.x.to_numpy()
    ind = np.where(img_req > 0)
    ax1.plot(x, y)

    x_req = np.take(x, ind)
    y_req = np.take(y, ind)
    ax1.scatter(x_req, y_req)

def animatedshmoo(i):
    df = pd.read_csv(log_file, names=["voltage", "frequency", "energy"], index_col=False)
    # voltage range is always 700 - 1100, tick is 50
    # frequency range is always 10 - 100, tick is 10
    # so we can pad the missing values
    df.set_index(["voltage", "frequency"], inplace=True)
    voltage_range = np.arange(700, 1100, 50)
    frequency_range = np.arange(10, 100, 10)
    df = df.reindex(pd.MultiIndex.from_product([voltage_range, frequency_range], names=["voltage", "frequency"]))
    df.reset_index(inplace=True)
    df.fillna(0, inplace=True)
    # magic number, 0 = not tested yet, -1 = failed
    # paint the shmoo plot
    # sns.set()
    # sns.set_context("paper")
    # sns.set_style("whitegrid")
    # sns.set_palette("bright")
    ax1.imshow(df.energy.to_numpy().reshape(len(voltage_range), len(frequency_range)), interpolation='nearest', origin='lower')
    ax1.set_xticks(np.arange(len(frequency_range)))
    ax1.set_yticks(np.arange(len(voltage_range)))
    ax1.set_xticklabels(frequency_range)
    ax1.set_yticklabels(voltage_range)
    ax1.set_xlabel("Frequency (MHz)")
    ax1.set_ylabel("Voltage (mV)")
    ax1.set_title("Energy (mJ)")
    for i in range(len(voltage_range)):
        for j in range(len(frequency_range)):
            text = ax1.text(j, i, df.energy.to_numpy().reshape(len(voltage_range), len(frequency_range))[i, j],
                        ha="center", va="center", color="w")

log_file = find_latest_log()
print("Plotting " + log_file)
ani = animation.FuncAnimation(fig, animatedshmoo, interval=1000)
plt.show()
