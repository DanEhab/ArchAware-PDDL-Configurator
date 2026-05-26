(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (spawn ?x)
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (ispoint ?x)
    (blocked ?x)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (ispoint ?newhead))
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (tailsnake ?newtail)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (ISADJACENT ?head ?newhead)
        (spawn ?spawnpoint)
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (spawn ?nextspawnpoint)
        (headsnake ?newhead)
        (ispoint ?spawnpoint)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (spawn ?spawnpoint))
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (spawn dummypoint)
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)
)