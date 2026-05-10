import React, { useEffect, useMemo, useState } from 'react';
import api from '../api/api';

type NavLink = {
    key: string;
    label: string;
    href: string;
    icon?: string;
};

type NavbarProps = {
    links?: NavLink[];
    onNavigate?: (href: string) => void;
};

export default function Navbar({ links, onNavigate }: NavbarProps) {
    const defaultLinks = useMemo<NavLink[]>(
        () => [
            { key: 'home', label: 'Home', href: '#/', icon: '🏠' },
            { key: 'about', label: 'About', href: '#/about', icon: 'ℹ️' },
            { key: 'contact', label: 'Contact', href: '#/contact', icon: '✉️' },
            { key: 'social', label: 'Social', href: '#/social', icon: '🌐' },
        ],
        [],
    );

    const navigationLinks = links ?? defaultLinks;
    const [info, setInfo] = useState<unknown>(null);
    const [infoError, setInfoError] = useState<string | null>(null);
    const [activeLink, setActiveLink] = useState<string>('#/');
    const [isOnline, setIsOnline] = useState(true);

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

    useEffect(() => {
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    function handleNavigation(href: string) {
        setActiveLink(href);
        onNavigate?.(href);
    }

    return (
        <nav aria-label="Main navigation" className="navbar">
            <div className="navbar__content">
                <div className="navbar__logo">
                    <span className="navbar__logo-icon">✨</span>
                    <span className="navbar__logo-text">AI Chat</span>
                </div>

                <ul className="navbar__links">
                    {navigationLinks.map((link) => (
                        <li key={link.key} className="navbar__item">
                            <a
                                href={link.href}
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleNavigation(link.href);
                                }}
                                className={`navbar__link ${
                                    activeLink === link.href ? 'navbar__link--active' : ''
                                }`}
                            >
                                {link.icon && <span className="navbar__icon">{link.icon}</span>}
                                <span className="navbar__label">{link.label}</span>
                                <span className="navbar__underline"></span>
                            </a>
                        </li>
                    ))}
                </ul>

                <div className="navbar__status">
                    <span
                        className={`navbar__status-indicator ${
                            isOnline ? 'navbar__status-indicator--online' : 'navbar__status-indicator--offline'
                        }`}
                    ></span>
                    <span className="navbar__status-text">{isOnline ? 'Online' : 'Offline'}</span>
                </div>
            </div>

            {infoError ? (
                <p role="status" className="navbar__error">
                    {infoError}
                </p>
            ) : null}
            {info ? <pre aria-label="api info" style={{ display: 'none' }}>{JSON.stringify(info, null, 2)}</pre> : null}
        </nav>
    );
}