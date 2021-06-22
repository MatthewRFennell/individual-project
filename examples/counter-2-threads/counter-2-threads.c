#include <stdio.h>
#include <pthread.h>

#define THREAD_COUNT 64
int counter = 0;

void *increment(void *arguments) {
	counter++;
	return NULL;
}

int main(void) {
	pthread_t threads[THREAD_COUNT];
	for (int i = 0; i < THREAD_COUNT; i++) {
		pthread_create(&threads[i], NULL, increment, NULL);
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		pthread_join(threads[i], NULL);
	}
	printf("Counter value is %d\n", counter);
	return counter;
}
