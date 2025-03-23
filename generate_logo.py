import matplotlib.pyplot as plt
import numpy as np

def generate_logo(day):
    t = np.linspace(0, 2 * np.pi, 100)
    x = np.sin(t + day)
    y = np.cos(t + day)

    plt.figure(figsize=(1.28, 1.28))  # 128x128 pixels
    plt.plot(x, y, 'b-', linewidth=2)
    plt.fill(x, y, 'b', alpha=0.3)
    plt.axis('equal')
    plt.axis('off')

    plt.savefig("static/logo.png", dpi=100)
    plt.close()

if __name__ == "__main__":
    generate_logo(0)
