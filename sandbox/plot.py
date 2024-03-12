import matplotlib.pyplot as plt


def plot_vertex_time_relationship(vertex_counts, texture_update_times):
    plt.plot(vertex_counts, texture_update_times, marker="o", linestyle="-")
    plt.title("Texture Update Time vs Vertex Count")
    plt.xlabel("Vertex Count")
    plt.ylabel("Texture Update Time (seconds)")
    plt.grid(True)
    plt.show()


# Example data
vertex_counts = [
    208038,
    8204889,
    23077254,
    32819268,
    37118973,
    62106051,
    92308863,
    112317447,
]
texture_update_times = [0.0003, 0.0128, 0.0628, 0.0431, 0.1125, 0.1624, 0.4652, 2.0551]

plot_vertex_time_relationship(vertex_counts, texture_update_times)
