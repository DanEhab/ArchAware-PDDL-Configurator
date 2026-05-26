(define (domain ricochet-robots)
(:requirements :strips :typing :negative-preconditions)

(:types
    robot - object
    cell - object
    direction - object
)

(:predicates
    (NEXT ?c - cell ?cnext - cell ?dir - direction)
    (BLOCKED ?c - cell ?dir - direction)
    (at ?r - robot ?c - cell)
    (is-moving ?r - robot ?dir - direction)
    (free ?c - cell)
    (nothing-is-moving)
)

(:action go
    :parameters (?r - robot ?dir - direction)
    :precondition
        (and
            (nothing-is-moving)
        )
    :effect
        (and
            (not (nothing-is-moving))
            (is-moving ?r ?dir)
        )
)

(:action step
    :parameters (?r - robot ?cfrom - cell ?cto - cell ?dir - direction)
    :precondition
        (and
            (is-moving ?r ?dir)
            (at ?r ?cfrom)
            (NEXT ?cfrom ?cto ?dir)
            (not (BLOCKED ?cfrom ?dir))
            (free ?cto)
        )
    :effect
        (and
            (at ?r ?cto)
            (free ?cfrom)
            (not (at ?r ?cfrom))
            (not (free ?cto))
        )
)

(:action stop-at-barrier
    :parameters (?r - robot ?cat - cell ?dir - direction)
    :precondition
        (and
            (is-moving ?r ?dir)
            (at ?r ?cat)
            (BLOCKED ?cat ?dir)
        )
    :effect
        (and
            (nothing-is-moving)
            (not (is-moving ?r ?dir))
        )
)

(:action stop-at-robot
    :parameters (?r - robot ?cat - cell ?cnext - cell ?dir - direction)
    :precondition
        (and
            (is-moving ?r ?dir)
            (at ?r ?cat)
            (NEXT ?cat ?cnext ?dir)
            (not (free ?cnext))
        )
    :effect
        (and
            (nothing-is-moving)
            (not (is-moving ?r ?dir))
        )
)
)