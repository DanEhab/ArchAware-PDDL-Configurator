(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (blocked ?x)
    (ispoint ?x)
    (nextsnake ?x ?y)
    (tailsnake ?x)
    (headsnake ?x)
    (spawn ?x)
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (nextsnake ?newtail ?tail)
        (tailsnake ?tail)
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (blocked ?newhead)
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
        (tailsnake ?newtail)
        (not (tailsnake ?tail))
        (nextsnake ?newhead ?head)
        (headsnake ?newhead)
        (not (headsnake ?head))
    )
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (headsnake ?head)
        (spawn dummypoint)
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (nextsnake ?newhead ?head)
        (headsnake ?newhead)
        (not (headsnake ?head))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (headsnake ?head)
        (spawn ?spawnpoint)
        (ISADJACENT ?head ?newhead)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (nextsnake ?newhead ?head)
        (headsnake ?newhead)
        (not (headsnake ?head))
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)
)