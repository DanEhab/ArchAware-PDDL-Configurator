(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    ;up down left right of a field
    (ISADJACENT ?x ?y)
    ;the last field of the snake
    (tailsnake ?x)
    ;the first field of the snake
    (headsnake ?x)
    ;pieces of the snake that are connected. from front to back
    (nextsnake ?x ?y)
    ;a field that is occupied by the snake or by an obstacle
    (blocked ?x)
    ;next point that will spawn
    (spawn ?x)
    ;point y will spawn after point x
    (NEXTSPAWN ?x ?y)
    ;a field that has a point that can be collected by the snake
    (ispoint ?x)
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
        (headsnake ?head)
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
    )
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (ispoint ?newhead)
        (spawn dummypoint)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (tailsnake ?newtail)
        (not (headsnake ?head))
        (not (blocked ?tail))
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)
)