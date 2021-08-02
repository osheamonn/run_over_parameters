import numpy as np
import argparse


def d_exp(h):
    return (np.exp(h) - np.exp(-h)) / (2 * h)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spacing", type=float, required=True)
    return parser.parse_args()


def run(spacing):
    with open("error.txt", "w") as f:
        f.write(str(abs(1.0 - d_exp(spacing))))


if __name__ == "__main__":
    run(**vars(parse_args()))
