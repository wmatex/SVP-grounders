#!/usr/bin/env python3

def weights_generate(items, first_item_weight):
    p = first_item_weight

    if p < 0.5:
        p = p + 2*(0.5-p)

    p_norm = 2*(p - 1/2)
    sum_w = 0
    n = len(items)
    weights = [0 for i in items]

    for i in range(len(items)):
        w = p_norm*((1-sum_w) - (1-sum_w)/n) + (1 - sum_w)/n

        sum_w = sum_w + w
        n = n - 1
        weights[i] = w

    if first_item_weight < 0.5:
        return list(reversed(weights))
    else:
        return weights


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    weights = []
    N = 10
    for w in np.arange(0, 1.1, 0.1):
        weights.append(range(N))
        weights.append(weights_generate(range(N), w))


    plt.plot(*[w for w in weights])
    plt.show()


