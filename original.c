#include <stdio.h>
#include <pthread.h>

#define THREAD_COUNT 2

int counter = 0;

void *increment(void *thread_number_argument) {
	int *thread_number = (int *) thread_number_argument;
	printf("Thread %d incremented counter to %d\n", *thread_number, ++counter);
}

int main(void) {
	pthread_t threads[THREAD_COUNT];
	int thread_numbers[THREAD_COUNT];
	for (int i = 0; i < THREAD_COUNT; i++) {
		thread_numbers[i] = i;
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		pthread_create(&threads[i], NULL, increment, &thread_numbers[i]);
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		pthread_join(threads[i], NULL);
	}
	return 0;
}
