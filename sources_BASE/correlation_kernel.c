
#include <math.h>

void kernel_correlation(double float_n, double data[100][80],
                        double corr[80][80], double mean[80],
                        double stddev[80]) {
    int i;
    int j;
    int k;
    double eps = 0.1;

    L0: for (j = 0; j < 80; j++) {
    // @slot __PIPE__L0
    // @slot __UNROLL__L0

        mean[j] = 0.0;

        L4: for (i = 0; i < 100; i++) {
        // @slot __PIPE__L4
        // @slot __UNROLL__L4

            mean[j] += data[i][j];
        }
        mean[j] /= float_n;
    }

    L1: for (j = 0; j < 80; j++) {
    // @slot __PIPE__L1
    // @slot __UNROLL__L1

        stddev[j] = 0.0;

        L5: for (i = 0; i < 100; i++) {
        // @slot __PIPE__L5
        // @slot __UNROLL__L5

            stddev[j] += pow(data[i][j] - mean[j], (double)2);
        }
        stddev[j] /= float_n;
        stddev[j] = sqrt(stddev[j]);
        /* The following in an inelegant but usual way to handle
                 near-zero std. dev. values, which below would cause a zero-
                 divide. */
        stddev[j] = (stddev[j] <= eps ? 1.0 : stddev[j]);
    }
    /* Center and reduce the column vectors. */

    L2: for (i = 0; i < 100; i++) {
    // @slot __PIPE__L2
    // @slot __UNROLL__L2

        L6: for (j = 0; j < 80; j++) {
        // @slot __PIPE__L6
        // @slot __UNROLL__L6

            data[i][j] -= mean[j];
            data[i][j] /= sqrt(float_n) * stddev[j];
        }
    }
    /* Calculate the m * m correlation matrix. */

    L3: for (i = 0; i < 80 - 1; i++) {
    // @slot __PIPE__L3
    // @slot __UNROLL__L3

        corr[i][i] = 1.0;

        L7: for (j = i + 1; j < 80; j++) {
        // @slot __PIPE__L7
        // @slot __UNROLL__L7

            corr[i][j] = 0.0;

            L8: for (k = 0; k < 100; k++) {
            // @slot __PIPE__L8
            // @slot __UNROLL__L8

                corr[i][j] += data[k][i] * data[k][j];
            }
            corr[j][i] = corr[i][j];
        }
    }
    corr[80 - 1][80 - 1] = 1.0;
}
