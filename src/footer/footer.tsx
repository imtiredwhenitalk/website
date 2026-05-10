import React from 'react';

export const Footer = () => {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="footer">
            <div className="footer__content">
                <div className="footer__section footer__section--info">
                    <div className="footer__header">
                        <span className="footer__icon">✨</span>
                        <h3 className="footer__title">AI Chat</h3>
                    </div>
                    <p className="footer__description">Modern AI chat interface with file support</p>
                </div>

                <div className="footer__section footer__section--links">
                    <h4 className="footer__section-title">Quick Links</h4>
                    <ul className="footer__links">
                        <li>
                            <a href="#/" className="footer__link">
                                Home
                            </a>
                        </li>
                        <li>
                            <a href="#/about" className="footer__link">
                                About
                            </a>
                        </li>
                        <li>
                            <a href="#/contact" className="footer__link">
                                Contact
                            </a>
                        </li>
                    </ul>
                </div>

                <div className="footer__section footer__section--contact">
                    <h4 className="footer__section-title">Contact</h4>
                    <div className="footer__contact-item">
                        <span className="footer__contact-icon">✉️</span>
                        <a href="mailto:sashamelnik360@gmail.com" className="footer__link">
                            sashamelnik360@gmail.com
                        </a>
                    </div>
                    <div className="footer__contact-item">
                        <span className="footer__contact-icon">🌐</span>
                        <span>Built with React & Python</span>
                    </div>
                </div>
            </div>

            <div className="footer__divider"></div>

            <div className="footer__bottom">
                <p className="footer__copyright">
                    © {currentYear} AI Chat. All rights reserved.
                </p>
                <div className="footer__social">
                    <a href="#" className="footer__social-link" title="GitHub">
                        🐙
                    </a>
                    <a href="#" className="footer__social-link" title="Twitter">
                        𝕏
                    </a>
                    <a href="#" className="footer__social-link" title="LinkedIn">
                        💼
                    </a>
                </div>
            </div>
        </footer>
    );
};