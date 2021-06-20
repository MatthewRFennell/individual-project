#include <stdio.h>
#include <pthread.h>

#define THREAD_COUNT 8
#define NON_INCREMENT_THREAD_COUNT 1
// @Syrup: shared-variable
int counter = 0;
int primes[] = {2, 3, 5, 7, 11, 13, 17, 19};
int last_created_thread = 1;

// @Syrup: entry-point
void *increment(void *arguments) {
	int thread_number = ++last_created_thread;
	int number_to_add = primes[thread_number - NON_INCREMENT_THREAD_COUNT - 1];
	counter += number_to_add;
}

int main(void) {
	pthread_t threads[THREAD_COUNT];
	int thread_numbers[THREAD_COUNT];
	for (int i = 0; i < THREAD_COUNT; i++) {
		thread_numbers[i] = i;
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		// @Syrup: thread-create
		pthread_create(&threads[i], NULL, increment, NULL);
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		// @Syrup: thread-join
		pthread_join(threads[i], NULL);
	}
	printf("Counter value is %d\n", counter);
	return 0;
}
