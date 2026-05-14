(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (headsnake ?x)
    (tailsnake ?x)
    (blocked ?x)
    (ispoint ?x)
    (spawn ?x)
    (nextsnake ?x ?y)
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
        (spawn dummypoint)
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (nextsnake ?newhead ?head)
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (tailsnake ?tail)
        (ISADJACENT ?head ?newhead)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (blocked ?newhead)
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (tailsnake ?newtail)
        (nextsnake ?newhead ?head)
        (not (nextsnake ?newtail ?tail))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (spawn ?spawnpoint)
        (ISADJACENT ?head ?newhead)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
        (nextsnake ?newhead ?head)
    )
)
)