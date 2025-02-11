import multiprocessing
import time

from arqmath_ import read
from math_text import generate_math_text


def generate_mlm_math_text_(start, len, i, arqmath):
    try:
        print("Start process: %d" % i)
        generate_math_text(questions_start=start, questions_len=len, arqmath=arqmath, amps=False, version='_arqmath_asynch_' + str(i), append=True, verbose=False)
    except Exception as e:
        print("EXCEPTION: %s" % e)
        raise e

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--processes', type=int, default=12)
    parser.add_argument('--batch', type=int, default=20000)
    parser.add_argument('--timeout', type=int, default=7 * 24 * 60 * 60)  # 1 week
    args = parser.parse_args()

    arqmath = read()
    n = len(arqmath.post_parser.map_questions)
    print("n=%d" % n)

    batch = args.batch
    iterations = (n + batch - 1) // batch  # Calculate the number of iterations including incomplete batch
    print("iterations = %d" % iterations)

    pool = multiprocessing.Pool(processes=args.processes)
    results = []

    for index, i in enumerate(range(0, n, batch)):
        print("Schedule run %d (processing items %d to %d)" % (index, i, min(i + batch, n)))
        result = pool.apply_async(generate_mlm_math_text_, (i, batch, index, arqmath))
        results.append(result)

    timeout_seconds = args.timeout
    start_time = time.time()

    # Process results with timeout handling
    try:
        for index, result in enumerate(results):
            elapsed_time = time.time() - start_time
            remaining_time = timeout_seconds - elapsed_time
            if remaining_time <= 0:
                print("Timeout reached. Exiting.")
                break
            print(f"Waiting for result {index} (timeout in {remaining_time:.2f} seconds)")
            processed_result = result.get(timeout=remaining_time)  # Wait for result with timeout
            # Optionally process `processed_result` here
    except multiprocessing.TimeoutError:
        print("A task timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Close and join the pool
    pool.close()
    pool.join()

    print("All tasks complete.")