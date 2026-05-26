(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (clear ?x - surface)
             (available ?x - hoist)
             (on ?x - crate ?y - surface)
             (lifting ?x - hoist ?y - crate)
             (in ?x - crate ?y - truck)
             (at ?x - locatable ?y - place))

(:action Lift
:parameters (?y - crate ?x - hoist ?z - surface ?p - place)
:precondition (and (on ?y ?z) (clear ?y) (at ?y ?p) (available ?x) (at ?x ?p))
:effect (and (not (on ?y ?z)) (not (clear ?y)) (clear ?z) (not (at ?y ?p)) (lifting ?x ?y) (not (available ?x))))

(:action Drop
:parameters (?y - crate ?x - hoist ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (clear ?z) (at ?z ?p) (at ?x ?p))
:effect (and (on ?y ?z) (clear ?y) (at ?y ?p) (not (clear ?z)) (available ?x) (not (lifting ?x ?y))))

(:action Load
:parameters (?y - crate ?x - hoist ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Unload
:parameters (?y - crate ?x - hoist ?z - truck ?p - place)
:precondition (and (in ?y ?z) (available ?x) (at ?x ?p) (at ?z ?p))
:effect (and (not (in ?y ?z)) (lifting ?x ?y) (not (available ?x))))

(:action Drive
:parameters (?x - truck ?y - place ?z - place)
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

)