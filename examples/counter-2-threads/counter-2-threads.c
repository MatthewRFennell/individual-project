#include <stdio.h>
#include <pthread.h>

#define THREAD_COUNT 4
// @Syrup: shared-variable
int counter = 0;

// @Syrup: entry-point
void *increment(void *arguments) {
	counter++;
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
