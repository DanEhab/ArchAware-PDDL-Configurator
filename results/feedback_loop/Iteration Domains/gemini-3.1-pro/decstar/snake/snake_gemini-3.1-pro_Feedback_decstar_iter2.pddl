(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (blocked ?x)
    (ispoint ?x)
    (tailsnake ?x)
    (headsnake ?x)
    (spawn ?x)
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
    (nextsnake ?x ?y)
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (spawn dummypoint)
    )
    :effect
    (and
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (headsnake ?newhead)
        (not (headsnake ?head))
        (nextsnake ?newhead ?head)
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (not (= ?spawnpoint dummypoint))
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (spawn ?spawnpoint)
    )
    :effect
    (and
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (headsnake ?newhead)
        (not (headsnake ?head))
        (nextsnake ?newhead ?head)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (blocked ?newhead)
        (not (blocked ?tail))
        (headsnake ?newhead)
        (not (headsnake ?head))
        (tailsnake ?newtail)
        (not (tailsnake ?tail))
        (nextsnake ?newhead ?head)
        (not (nextsnake ?newtail ?tail))
    )
)
)