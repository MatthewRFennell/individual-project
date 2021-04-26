#include <stdio.h>
#include <stdlib.h>

// Counter defines
#define THREAD_COUNT 2

// Syrup defines
#define MAX_THREAD_COUNT (THREAD_COUNT + 1)
#define DEFAULT_THREAD_STACK_SIZE 1024

// Declarations
int next_thread_id;

// Syrup interface
typedef struct syrup_pthread_t {
	int id;
	void *(*start_routine)(void *);
	void *stack;
	int current_position;
} syrup_pthread_t;

typedef struct syrup_pthread_attr_t {
} syrup_pthread_attr_t;

int syrup_pthread_create(syrup_pthread_t *thread, const syrup_pthread_attr_t *attr,
		void *(*start_routine) (void *), void *arg) {
	thread->id = next_thread_id++;
	thread->start_routine = start_routine;
	thread->stack = malloc(DEFAULT_THREAD_STACK_SIZE);
	return 0;
}

int syrup_pthread_join(syrup_pthread_t thread, void **retval) {
	return 0;
}

// Syrup internals
int next_thread_id = 0;

typedef struct thread_manager_t {
	syrup_pthread_t threads[MAX_THREAD_COUNT];
} thread_manager_t;

// Non-Syrup
int counter = 0;

void *increment_counter(void *thread_number_argument) {
	int *thread_number = (int *) thread_number_argument;
	printf("Thread %d incremented counter to %d\n", *thread_number, ++counter);
}

int original_main(void) {
	syrup_pthread_t threads[THREAD_COUNT];
	int thread_numbers[THREAD_COUNT];
	for (int i = 0; i < THREAD_COUNT; i++) {
		thread_numbers[i] = i;
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		syrup_pthread_create(&threads[i], NULL, increment_counter, &thread_numbers[i]);
	}
	for (int i = 0; i < THREAD_COUNT; i++) {
		syrup_pthread_join(threads[i], NULL);
	}
	return 0;
}

int main(void) {
	int result = original_main();
	return result;
}
