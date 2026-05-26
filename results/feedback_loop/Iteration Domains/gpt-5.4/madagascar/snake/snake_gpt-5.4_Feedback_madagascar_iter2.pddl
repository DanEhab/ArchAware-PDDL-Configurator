(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (ispoint ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (ISADJACENT ?head ?newhead)
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

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (spawn dummypoint)
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
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

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
    )
)

)