#include <stdio.h>
#include <pthread.h>

#define THREAD_COUNT 2

int counter = 0;

void *increment(void *arguments) {
	counter++;
}

int main(void) {
	pthread_t threads[THREAD_COUNT];
	pthread_t thread1;
	pthread_t thread2;
	for (int i = 0; i < THREAD_COUNT; i++) {
		pthread_create(&threads[i], NULL, increment, NULL);
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		pthread_join(threads[i], NULL);
	}
	return 0;
}
