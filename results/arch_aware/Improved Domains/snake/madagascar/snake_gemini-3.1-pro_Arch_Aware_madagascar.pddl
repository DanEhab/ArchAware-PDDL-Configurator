(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (spawn ?x)
    (ispoint ?x)
    (headsnake ?x)
    (tailsnake ?x)
    (blocked ?x)
    (nextsnake ?x ?y)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
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
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (not (= ?spawnpoint dummypoint))
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (ISADJACENT ?head ?newhead)
        (spawn ?spawnpoint)
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (nextsnake ?newtail ?tail)
        (headsnake ?head)
        (tailsnake ?tail)
        (not (ispoint ?newhead))
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (tailsnake ?newtail)
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)
)