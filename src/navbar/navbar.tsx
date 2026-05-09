import React, { useEffect, useMemo, useState } from 'react';
import api from '../api/api';

type NavLink = {
    key: string;
    label: string;
    href: string;
};

type NavbarProps = {
    links?: NavLink[];
    onNavigate?: (href: string) => void;
};

export default function Navbar({ links, onNavigate }: NavbarProps) {
    const defaultLinks = useMemo<NavLink[]>(
        () => [
            { key: 'home', label: 'Home', href: '#/' },
            { key: 'about', label: 'About', href: '#/about' },
            { key: 'contact', label: 'Contact', href: '#/contact' },
            { key: 'social', label: 'Social', href: '#/social' },
        ],
        [],
    );

    const navigationLinks = links ?? defaultLinks;

    const [info, setInfo] = useState<unknown>(null);
    const [infoError, setInfoError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        (async () => {
            const result = await api.get('/info');
            if (cancelled) return;

            if (!result.ok) {
                setInfoError('Failed to fetch /info');
                return;
            }

            setInfo(result.data);
        })();

        return () => {
            cancelled = true;
        };
    }, []);

    function handleNavigation(href: string) {
        onNavigate?.(href);
    }

    return (
        <nav aria-label="Main navigation">
            <ul>
                {navigationLinks.map((link) => (
                    <li key={link.key}>
                        <a href={link.href} onClick={() => handleNavigation(link.href)}>
                            {link.label}
                        </a>
                    </li>
                ))}
            </ul>
            {infoError ? <p role="status">{infoError}</p> : null}
            {info ? (
                <pre aria-label="api info">{JSON.stringify(info, null, 2)}</pre>
            ) : null}
        </nav>
    );
}