import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
#print("plot_data wurde aufgerufen")

def plot_data(df):
    x = df.iloc[:, 0]
    y = df.iloc[:, 1]

    plt.figure()
    plt.plot(x, y)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Erster Plot")
    plt.show()