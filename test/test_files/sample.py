import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--i", required=True)
    parser.add_argument("--j", required=True)
    parser.add_argument("--k", required=True)
    return parser.parse_args()


def run(i, j, k):
    with open("output.txt", "w") as f:
        f.write("{i}{j}{k}".format(i=i, j=j, k=k))


if __name__ == "__main__":
    run(**vars(parse_args()))
